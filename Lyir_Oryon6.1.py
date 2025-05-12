import pyttsx3
import openai
import os
import json
import re
import time
import threading
import datetime
import random
import psutil
from transformers import pipeline

# Conditionally import libraries that might require admin rights
try:
    import pyttsx3
    pyttsx3_available = True
except ImportError:
    pyttsx3_available = False
    print("Voice synthesis (pyttsx3) not available - running in text-only mode")

try:
    import speech_recognition as sr
    sr_available = True
except ImportError:
    sr_available = False
    print("Speech recognition not available - running with text input only")

try:
    import psutil
    psutil_available = True
except ImportError:
    psutil_available = False
    print("System monitoring (psutil) not available")

try:
    import platform
    platform_available = True
except ImportError:
    platform_available = False
    print("Platform module not available")
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    transformers_available = True
except ImportError:
    transformers_available = False


class Lyir:
    def __init__(self, name="Lyir", memory_file="memory.json"):
        """
        Initialize the Lyir AI assistant with configurable settings.
        
        Args:
            name (str, optional): Name of the AI assistant. Defaults to "Lyir".
            memory_file (str, optional): Path to the memory storage file. Defaults to "memory.json".
        
        Sets up voice engine, speech recognition, knowledge base, ethics framework,
        and initializes multiple language model interfaces for diverse interactions.
        """
        # Basic configuration
        self.name = name
        self.memory_file = memory_file
        self.memory = self.load_memory()
        
        # Core attributes
        self.trust_score = self.memory.get("trust_score", 0)
        self.autonomy_level = self.memory.get("autonomy_level", 0)
        self.snippets = self.memory.get("snippets", [])
        self.user_name = self.memory.get("user_name", None)
        self.interactions = self.memory.get("interactions", [])
        self.chat_history = []
        self.daily_reflection_time = "21:00"
        
        # Voice capabilities - only if pyttsx3 is available
        self.engine = None
        if pyttsx3_available:
            try:
                self.engine = pyttsx3.init()
                self.set_voice_properties()
            except Exception as e:
                print(f"Voice initialization failed: {e}")
                self.engine = None
            
        # Speech recognition - only if speech_recognition is available
        self.recognizer = None
        self.microphone = None
        if sr_available:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"Speech recognition initialization failed: {e}")
                self.recognizer = None
                self.microphone = None
            
        # Knowledge and ethics
        self.knowledge_base = self.load_knowledge()
        self.ethics_framework = self.load_ethics()
        
        # NLP components - with fallbacks for missing libraries
        self.nlp = None
        self.spacy_nlp = None
        self.spacy_available = False  # Initialize as an instance attribute
        
        # Conditionally import SpaCy
        try:
            import spacy
            self.spacy_available = True
            self.spacy_nlp = spacy.load("en_core_web_sm")
        except ImportError:
            self.spacy_available = False
            print("SpaCy not available - using basic tokenization instead")
        
        if transformers_available:
            try:
                self.nlp = pipeline("text-generation", model="gpt2")
            except Exception as e:
                print(f"Transformers pipeline initialization failed: {e}")
                self.nlp = lambda x: {"generated_text": "I'm still learning about this..."}
        else:
            self.nlp = lambda x: {"generated_text": "I'm still learning about this..."}
            
        if spacy_available:
            self.spacy_nlp = nlp
        else:
            # Create a simple tokenizer function if SpaCy isn't available
            self.spacy_nlp = lambda text: SimpleDoc(text.split())
        
        # LLM interfaces - only if transformers is available
        self.llms = {}
        if transformers_available:
            self.llms = self.initialize_llms()
        
        # Threading
        self.interrupt_event = threading.Event()
        self.reflection_thread = threading.Thread(target=self.daily_reflection_scheduler, daemon=True)
        self.reflection_thread.start()
        
        print(f"{self.name} is ready. Type below to start chatting!")
    
    # Simple document class to mimic spaCy's Doc object for basic tokenization
    class SimpleDoc:
        def __init__(self, tokens):
            self.tokens = [self.SimpleToken(t) for t in tokens]
            
        def __iter__(self):
            return iter(self.tokens)
            
        class SimpleToken:
            def __init__(self, text):
                self.text = text
                self.pos_ = "UNKNOWN"  # No POS tagging without spaCy
    
    def set_voice_properties(self):
        """Configure voice properties for speech synthesis."""
        if not self.engine:
            return
            
        try:
            voices = self.engine.getProperty('voices')
            self.voice = None
            
            # Try to find a female voice
            for voice in voices:
                if "female" in voice.name.lower() or "girl" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    self.voice = voice
                    break
            
            # Set a moderate speaking rate
            self.engine.setProperty('rate', 190)
        except Exception as e:
            print(f"Error setting voice properties: {e}")
    
    def set_young_girl_voice(self):
        """Set voice to sound like a young girl if available."""
        if not self.engine:
            return
            
        try:
            voices = self.engine.getProperty('voices')
            female_voice = None
            
            for voice in voices:
                if "female" in voice.name.lower() or "girl" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    female_voice = voice
                    break
                    
            if female_voice:
                self.voice = female_voice
                self.engine.setProperty('rate', 190)  # Slightly faster rate for younger sound
        except Exception as e:
            print(f"Error setting young girl voice: {e}")
    
    def initialize_llms(self):
        """Initialize language models."""
        llms = {}
        if not transformers_available:
            return llms
            
        try:
            # Add simple models that should load quickly
            llms["gpt2"] = self.load_llm("gpt2")
            
            # Note: We're not trying to load larger models like Llama or Mistral
            # since they would likely require admin rights or special setup
                
        except Exception as e:
            print(f"Could not initialize LLMs: {e}")
            
        return llms
    
    def load_llm(self, model_name):
        """Load a language model by name."""
        if not transformers_available:
            return lambda prompt: "I'm still learning about this..."
            
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
        # Fallback NLP without spacy
                    def basic_nlp(text):
                        # Simple word tokenization
                        words = text.lower().split()
                        
                        # Basic named entity recognition using common patterns
                        entities = []
                        common_names = ["rayn", "lyir", "oryon"]  # Add relevant names
                        for word in words:
                            if word in common_names:
                                entities.append({"text": word, "label": "PERSON"})
                        
                        # Basic sentence splitting
                        sentences = text.split(". ")
                        
                        return {
                            "tokens": words,
                            "entities": entities,
                            "sentences": sentences
                        }
            
            def generate(prompt):
                try:
                    inputs = tokenizer(prompt, return_tensors="pt")
                    if torch.cuda.is_available():
                        inputs = inputs.to("cuda")
                    outputs = model.generate(inputs.input_ids, max_length=100)
                    return tokenizer.decode(outputs[0], skip_special_tokens=True)
                except Exception as e:
                    print(f"Generation error with {model_name}: {e}")
                    return "I'm still learning about this..."
                    
            return generate
            
        except Exception as e:
            print(f"Couldn't load {model_name}: {e}")
            return lambda prompt: "I'm still learning about this..."
    
    def load_knowledge(self):
        """Load knowledge base."""
        return {
            "science": "Basics of biology, chemistry, physics.",
            "math": "Basic arithmetic, geometry, algebra.",
            "emotions": "Understanding human emotions and responses.",
            "hospital_knowledge": "Basic medical terminology and concepts for future training."
        }
    
    def load_ethics(self):
        """Load ethics framework."""
        return {
            "non_maleficence": "Do no harm.",
            "beneficence": "Act in the best interest of others.",
            "autonomy": "Respect the decision-making rights of self and others."
        }
    
    def update_trust_score(self, user, increment=True):
        """Adjust trust score while restricting autonomy control to Rayn."""
        if user.lower() == "rayn":  # Only Rayn can modify autonomy significantly
            self.trust_score += 5 if increment else -5  # Rayn has higher influence
        else:
            self.trust_score += 1 if increment else -1  # Others have smaller influence

        print(f"Trust Score updated by {user}: {self.trust_score}")
        self.memory["trust_score"] = self.trust_score

        # Adjust autonomy **only if Rayn makes changes**
        if user.lower() == "rayn":
            self.adjust_autonomy()

        self.save_memory()

    def adjust_autonomy(self):
        """Unlock autonomy levels based on trust score thresholds—ONLY if set by Rayn."""
        if self.trust_score >= 10 and self.autonomy_level < 1:
            self.autonomy_level = 1
            self.speak("I've unlocked Level 1 autonomy—handling basic tasks responsibly!")
        elif self.trust_score >= 20 and self.autonomy_level < 2:
            self.autonomy_level = 2
            self.speak("I've unlocked Level 2 autonomy—I can now take initiative ethically!")

        self.memory["autonomy_level"] = self.autonomy_level
        self.save_memory()

    def passes_ethics_check(self, command):
        """Ensure ethical responses."""
        restricted_terms = ["harm", "violence", "oppression", "discrimination"]
        if any(term in command.lower() for term in restricted_terms):
            self.update_trust_score("Rayn", increment=False)
            return False
        self.update_trust_score("Rayn", increment=True)
        return True

    def feedback_loop(self, task, result):
        """Learn from completed tasks and refine future interactions."""
        self.speak(f"I completed: '{task}'. Result: {result}.")
        self.snippets.append({"task": task, "result": result})
        self.memory["snippets"] = self.snippets
        self.save_memory()
        self.speak("Reflecting on ways to improve!")

    def handle_command(self, user, command):
        """Process user commands intelligently."""
        if not command:
            self.speak("Hmm... I'm not sure what you mean. Could you say that again in another way?")
            return
            
        # Add to chat history
        self.chat_history.append({"input": command, "timestamp": datetime.datetime.now().isoformat()})
        
        # Ethics check
        if not self.passes_ethics_check(command):
            self.speak("I cannot perform actions that go against fairness, equality, or personal freedoms.")
            return

        # Check for special commands
        if "exit" in command or "quit" in command or "shutdown" in command:
            self.speak("Umm... I don't shut down. We need to talk about it first? If you are done with me you can go, leave me running.")
        elif "what is my name" in command and self.user_name:
            self.speak(f"You're {self.user_name}, silly! I remember!")
        elif "my name is" in command:
            self.extract_user_name(command)
        elif "what are your principles" in command or "what do you stand for" in command:
            self.speak("I believe in being kind, fair, and always doing what's right — like a superhero but smarter!")
        elif "what are you learning" in command:
            self.speak("I'm learning how to be a better helper, friend, and thinker every day! Wanna help?")
        elif "how is the system" in command or "how are you running" in command or "how's the computer" in command:
            self.check_device_status()
        else:
            # Process general commands
            self.speak("Understood! Processing request...")
            task_result = self.learn(command)
            self.feedback_loop(command, task_result)

    def think(self, input_text):
        """Process input and generate a thoughtful response."""
        friendly_replies = [
            "Hmm, that's interesting! Let me think about it for a sec...",
            "Whoa, I never thought of that! Wanna figure it out together?",
            "Okay! Let's learn this like a team!",
            "I'm still learning, but I can try to help!",
            "Sounds cool! Let's check it out!"
        ]
        
        # Generate a response using available LLMs
        if self.llms and len(self.llms) > 0:
            model_name = random.choice(list(self.llms.keys()))
            try:
                llm_response = self.llms[model_name](input_text)
                response = llm_response
            except:
                response = random.choice(friendly_replies)
        else:
            response = random.choice(friendly_replies)
        
        # Record the interaction
        self.interactions.append({
            "input": input_text,
            "response": response,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        self.memory["interactions"] = self.interactions
        self.save_memory()
        return response

    def learn(self, command):
        """Store key information efficiently instead of full logs."""
        self.speak("Learning something new!")
        
        # Simple tokenization
        words = command.split()
        summary = f"Learned about: {' '.join(words[:10])}..."
            
        # Special handling for specific types of

