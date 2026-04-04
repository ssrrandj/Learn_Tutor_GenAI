from gtts import gTTS

def speak_answer(text):
    file = "answer.mp3"
    gTTS(text).save(file)
    return file