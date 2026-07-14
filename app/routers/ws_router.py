"""Streaming turn endpoint over WebSocket (Section 21 NFR: first token <2.5s p50).
Tokens are streamed to the client as they arrive; the Answer-Leak Guard still
runs on the FULL buffered message before the turn is considered final — if a
leak is detected we send a `correction` event with the safe replacement."""
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.agents import diagnostic_agent, heuristics, misconception_agent, socratic_agent
from app.agents.answer_leak_guard import check_leak
from app.auth import get_current_user
from app.config import settings
from app.database import AsyncSessionLocal
from app.hint_ladder import next_tier, tier_instruction
from app.jwt_ws import get_user_from_token
from app.llm_client import chat_stream
from app.mode_selector import select_mode
from app.models import Concept, LearningSession, SessionTurn
from app.orchestrator import FALLBACK_HINT_TEMPLATE
from app.redis_client import append_message, get_working_memory
from app.state_machine import LearnerState, Signals, transition

router = APIRouter()


@router.websocket("/v1/ws/session/{session_id}/turn")
async def ws_turn(websocket: WebSocket, session_id: uuid.UUID, token: str):
    await websocket.accept()
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as db:
        session = await db.get(LearningSession, session_id)
        if not session or session.user_id != user.id:
            await websocket.close(code=4404)
            return
        concept = await db.get(Concept, session.concept_id)

        try:
            while True:
                raw = await websocket.receive_text()
                student_message = json.loads(raw)["message"]

                mem = await get_working_memory(str(session_id))
                recent_turns = mem["messages"]
                await append_message(str(session_id), "student", student_message)

                diag = await diagnostic_agent.run_diagnostic(concept.name, recent_turns, student_message)
                misc = await misconception_agent.run_misconception_check(
                    concept.name, concept.canonical_facts, student_message
                )
                stuck = heuristics.is_stuck_signal(student_message)
                signals = Signals(
                    confidence=heuristics.aggregate_confidence(diag.get("confidence", 0.5),
                                                                heuristics.hedge_word_frequency(student_message),
                                                                1.0 if diag.get("correct_baseline") else 0.5),
                    misconception_flag=bool(misc.get("misconception")),
                    stuck=stuck,
                    contradiction=bool(misc.get("misconception")),
                    correct_baseline=bool(diag.get("correct_baseline")),
                    shared_ai_usage=bool(diag.get("shared_ai_usage")),
                )
                prev_state = LearnerState(session.current_state)
                new_state, unresolved = transition(prev_state, session.unresolved_turns, signals)
                mode = select_mode(new_state, signals, None, concept.domain)
                new_tier = next_tier(session.hint_tier, stuck)

                await websocket.send_json({"event": "meta", "state": new_state.value, "mode": mode, "hint_tier": new_tier})

                system = f"Concept: {concept.name}. Mode: {mode}. {tier_instruction(new_tier)}"
                history = [{"role": "user" if t["role"] == "student" else "assistant", "content": t["content"]}
                           for t in recent_turns[-8:]]
                messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": student_message}]

                buffer = ""
                async for token_piece in chat_stream(messages, model=settings.LLM_MODEL):
                    buffer += token_piece
                    await websocket.send_json({"event": "token", "data": token_piece})

                leaked, _ = await check_leak(buffer)
                final_text = buffer
                if leaked:
                    final_text = FALLBACK_HINT_TEMPLATE
                    await websocket.send_json({"event": "correction", "data": final_text})

                db.add(SessionTurn(session_id=session.id, role="student", content=student_message,
                                    mode=mode, hint_tier=new_tier, learner_state=new_state.value))
                db.add(SessionTurn(session_id=session.id, role="tutor", content=final_text,
                                    mode=mode, hint_tier=new_tier, learner_state=new_state.value))
                session.current_state = new_state.value
                session.current_mode = mode
                session.hint_tier = new_tier
                session.unresolved_turns = unresolved
                db.add(session)
                await db.commit()
                await append_message(str(session_id), "tutor", final_text)

                await websocket.send_json({"event": "done"})
        except WebSocketDisconnect:
            pass
