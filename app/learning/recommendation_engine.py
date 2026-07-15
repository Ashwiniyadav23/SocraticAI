import logging

logger = logging.getLogger("recommendation_engine")

def generate_recommendations(user_profile, weak_areas):
    """
    Given a user's profile and identified weak areas from the Reflection Graph,
    returns a list of recommended topics or tasks.
    """
    recommendations = []
    if weak_areas:
        for area in weak_areas:
            recommendations.append({
                "type": "review_doc",
                "topic": area,
                "reason": "Identified as a weak area in recent mastery checks."
            })
    return recommendations
