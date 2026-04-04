def detect_subject(text):
    text = text.lower()

    if any(w in text for w in ["+", "-", "*", "/", "=", "Solve", "euation"]):

        return "math"
    
    elif any(w in text for w in ["poem", "rhyme", "verse"]):

        return "rhyme"
    
    elif any(w in text for w in ["force", "energy", "motion", "gravity"]):

        return "physics"
    
    elif any(w in text for w in ["atom", "molecule", "acid", "reaction"]):

        return "chemistry"
    
    else:

        return "general"