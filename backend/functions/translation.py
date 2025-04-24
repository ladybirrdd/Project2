from transformers import MarianMTModel, MarianTokenizer
import random

# Load model and tokenizer only once
model_name = 'Helsinki-NLP/opus-mt-en-hi'
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Function to simulate beginner-level typos and errors, including Chandrabindu removal
def introduce_typo(word):
    beginner_errors = {
        "हूँ": "ह",   
        "मैं": "म",    
        "है": "ह",      
        "जा रहा": "चल",  
        "अब": "अभी",     
        "के लिए": "लिए",  
        "बाजार": "घार",   
        "यह": "वह",      
        "घर": "घार",      
        "है": "था",      
        "हूँ": "ह",      
        "मैं": "मझ",      
        "हैं": "ह",      
        "कहाँ": "कहा",   
    }

    if word in beginner_errors:
        return beginner_errors[word]
    return word

# Function to simulate a beginner-level noisy translation model
def bad_but_meaningful_translate(text):
    # Translate the English text to Hindi using MarianMTModel
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    translated_tokens = model.generate(**inputs)
    translation = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

    words = translation.split()
    final_translation = []
    extra_hindi_words = ["ठीक", "बस", "कभी", "देखो", "यहां", "अभी", "शायद", "जल्दी", "फिर", "मौसम",
                         "हां", "कहाँ", "बिलकुल", "क्यों", "अच्छा", "जाने", "सपना", "काम", "बात",
                         "सुबह", "रात", "दिन", "खुश", "दुख", "भूख", "खेल", "गाना", "नींद", "पढ़ाई",
                         "दोस्त", "परिवार", "शहर", "गाड़ी", "पानी", "सड़क", "सपना", "खत्म", "कहानी",
                         "सच्चाई", "अंधेरा", "रोशनी", "जंगल", "पेड़", "पत्ता", "हवा", "धूप", "बारिश",
                         "सर्दी", "गर्मी", "छाता", "सड़क", "डर", "प्यार", "आशा", "खुशी", "मन", "शांत",
                         "शब्द", "भावना", "शक्ति", "संगीत", "नृत्य", "चित्र", "रंग", "दुनिया", "सफर",
                         "मंजिल", "रास्ता", "पल", "सपना", "ख्वाब", "तस्वीर", "चेहरा", "हाथ", "पैर",
                         "आंख", "दिल", "दिमाग", "सवाल", "जवाब", "झील", "नदी", "समय", "धैर्य",
                         "उम्मीद", "ताकत", "आवाज", "शोर", "खामोशी", "अद्भुत", "बोल", "कर", "चलो",
                         "ठहर", "सोच", "सीख", "सुन", "हँस", "रो", "जीत", "हार"]

    for word in words:
        # Apply beginner-level typos and errors
        word = introduce_typo(word)
        final_translation.append(word)

    # Occasionally swap word order or miss an auxiliary verb (15% chance)
    if random.random() < 0.15:
        idx = random.randint(0, len(final_translation) - 2)
        final_translation[idx], final_translation[idx + 1] = final_translation[idx + 1], final_translation[idx]

    # Occasionally insert some extra, unnecessary words (20% chance to add filler words)
    if random.random() < 0.2:  
        final_translation.insert(random.randint(0, len(final_translation)), random.choice(extra_hindi_words))

    # Occasionally remove a word (10% chance to drop a word)
    if random.random() < 0.1:  
        if len(final_translation) > 1:
            final_translation.pop(random.randint(0, len(final_translation)-1))

    # Keep original word order mostly intact, only minor shuffling allowed
    final_sentence = " ".join(final_translation)
    return final_sentence

# Function to translate English text to noisy Hindi
def translate_text_to_hindi(english_text):
    try:
        noisy_translation = bad_but_meaningful_translate(english_text)
        return noisy_translation
    except Exception as e:
        print(f"Error in translation to Hindi: {e}")
        return None
