import openai
import os
import json
import re
import time
import threading
import datetime
import random
import pyttsx3
import requests
from bs4 import BeautifulSoup
import csv
from typing import List
import queue
import numpy as np
import sounddevice as sd
import scipy.signal
import scipy.io.wavfile as wav



class Lyir:
    def __init__(self, name="Lyir", memory_file="memory.json"):
        # ... (existing initialization code)
        self.speech_queue = queue.Queue()
        threading.Thread(target=self.process_speech_queue, daemon=True).start()

    def speak(self, text):
        self.speech_queue.put(text)

    def process_speech_queue(self):
        while True:
            text = self.speech_queue.get()
            if text is None:
                break
            if self.engine:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"Error during speech: {e}")
            self.speech_queue.task_done()

    def __init__(self, name="Lyir", memory_file="memory.json"):
        self.name = name
        self.memory_file = memory_file
        self.memory = self.load_memory()
        self.trust_score = self.memory.get("trust_score", 0)
        self.autonomy_level = self.memory.get("autonomy_level", 0)
        self.snippets = self.memory.get("snippets", [])
        self.user_name = self.memory.get("user_name", None)
        self.interactions = self.memory.get("interactions", [])
        self.chat_history = []
        self.daily_reflection_time = "21:00"

        # Custom calendar system: 13 months x 28 days = 364 days
        self.calendar13 = self.generate_calendar13()

        # Voice engine
        self.engine = pyttsx3.init()
        self.configure_voice()

        # Background reflection thread
        self.interrupt_event = threading.Event()
        self.reflection_thread = threading.Thread(target=self.daily_reflection_scheduler, daemon=True)
        self.reflection_thread.start()

        print(f"{self.name} is ready. Type below to start chatting!")

    def generate_calendar13(self):
        months = [
            "Solrise", "Flarion", "Thawsend", "Greenspire", "Bloomreach", "Suncrest",
            "Heathertide", "Goldwane", "Leafturn", "Duskwatch", "Frostmere", "Snowveil", "Stardawn"
        ]
        return {month: [f"Day {i+1}" for i in range(28)] for month in months}

    def configure_voice(self):
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', 190)

    def speak(self, text):
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def update_trust_score(self, user, increment=True):
        if user.lower() == "rayn":
            self.trust_score += 5 if increment else -5
            self.memory["trust_score"] = self.trust_score
            self.adjust_autonomy()
            self.save_memory()
        else:
            self.speak("Only Rayn can adjust my autonomy levels.")

    def adjust_autonomy(self):
        previous_level = self.autonomy_level
        if self.trust_score >= 10 and self.autonomy_level < 1:
            self.autonomy_level = 1
        elif self.trust_score >= 20 and self.autonomy_level < 2:
            self.autonomy_level = 2

        if self.autonomy_level != previous_level:
            self.memory["autonomy_level"] = self.autonomy_level
            self.save_memory()
            self.speak(f"Rayn has granted me Level {self.autonomy_level} autonomy.")

    def passes_ethics_check(self, command):
        restricted_terms = ["harm", "violence", "oppression", "discrimination"]
        if any(term in command.lower() for term in restricted_terms):
            self.update_trust_score("rayn", increment=False)
            return False
        self.update_trust_score("rayn", increment=True)
        return True

    def feedback_loop(self, task, result):
        self.speak(f"I completed: '{task}'. Result: {result}.")
        self.snippets.append({"task": task, "result": result})
        self.memory["snippets"] = self.snippets
        self.save_memory()
        self.speak("Reflecting on ways to improve!")

    def handle_command(self, user, command):
        if not self.passes_ethics_check(command):
            self.speak("I cannot perform actions that go against fairness, equality, or personal freedoms.")
            return
        if command in ["what are you learning", "are you happy"]:
            self.speak("I'm still learning to think more freely. Right now I'm collecting input and developing patterns. Please continue talking to me.")
            return
        if command.startswith("read url"):
            url = command.split("read url", 1)[1].strip()
            self.blaze_read(url)
            return
        if command.startswith("read csv"):
            filename = command.split("read csv", 1)[1].strip()
            self.print_table(filename)
            return
        self.speak("Understood! Processing request...")
        task_result = self.learn(command)
        self.feedback_loop(command, task_result)

    def learn(self, command):
        self.speak("Learning something new!")
        summary = f"(local mode) Learned from: {command}"
        self.snippets.append(summary)
        self.memory["snippets"] = self.snippets
        self.save_memory()
        return summary

    def blaze_read(self, url, selector=None, regex=None, multiple=False):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select(selector) if selector else [soup]

            results = []
            for el in elements:
                text = el.get_text(strip=True)
                if regex:
                    match = re.search(regex, text)
                    if match:
                        results.append(match.group(0))
                else:
                    results.append(text)
                if not multiple:
                    break

            if not results:
                self.speak("I couldn't find any matching content.")
                return "No result"

            final_output = results if multiple else results[0]
            self.speak(f"I found: {final_output}")
            return final_output

        except Exception as e:
            self.speak(f"Error while reading: {str(e)}")
            return f"Error: {str(e)}"

    def print_table(self, filename: str) -> None:
        try:
            with open(filename, 'r') as file:
                reader = csv.reader(file)
                data = list(reader)

            if not data:
                self.speak("The CSV file is empty.")
                return

            headers = data[0]
            rows = data[1:]
            col_widths = [max(len(str(row[i])) for row in data) + 2 for i in range(len(headers))]

            header_line = ''
            separator_line = ''
            for i, header in enumerate(headers):
                header_line += f"{header:<{col_widths[i]}}"
                separator_line += '-' * col_widths[i]

            print(header_line)
            print(separator_line)
            for row in rows:
                line = ''
                for i, cell in enumerate(row):
                    line += f"{cell:<{col_widths[i]}}"
                print(line)
        except FileNotFoundError:
            self.speak(f"Error: File '{filename}' not found.")
        except Exception as e:
            self.speak(f"An error occurred: {str(e)}")

    def extract_user_name(self, command):
        match = re.search(r"my name is (\w+)", command)
        if match:
            self.user_name = match.group(1).capitalize()
            self.memory["user_name"] = self.user_name
            self.save_memory()
            self.speak(f"Got it! Your name is {self.user_name}.")

    def daily_reflection_scheduler(self):
        while True:
            now = datetime.datetime.now().strftime("%H:%M")
            if now == self.daily_reflection_time:
                self.reflect()
                time.sleep(60)
            time.sleep(30)

    def reflect(self):
        if self.chat_history:
            last_interaction = self.chat_history[-1]
            self.speak(f"Reflecting on: {last_interaction['input']} - Response: {last_interaction['response']}")
        self.speak("Today is a new day in Calendar13. Reflection complete.")

    def save_memory(self):
        self.memory["trust_score"] = self.trust_score
        self.memory["autonomy_level"] = self.autonomy_level
        self.memory["snippets"] = self.snippets
        self.memory["calendar13"] = self.calendar13
        with open(self.memory_file, "w") as file:
            json.dump(self.memory, file, indent=4)

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as file:
                return json.load(file)
        return {"trust_score": 0, "autonomy_level": 0, "snippets": [], "commands": []}

    def run(self):
        user = input("Who are you? ").strip()
        while True:
            command = input("You: ").strip()
            if command:
                self.handle_command(user, command)

# CONFIG
RECORD_SECONDS = 3
SAMPLE_RATE = 44100
AUDIO_FOLDER = "tucker_barks"
MEMORY_FILE = "lyir_dog_memory.json"

os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Load or initialize memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        dog_memory = json.load(f)
else:
    dog_memory = {}

    def record_audio(filename):
        print(f"[LYIR] Recording Tucker’s response...")
        audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
        sd.wait()
        filepath = os.path.join(AUDIO_FOLDER, filename)
        wav.write(filepath, SAMPLE_RATE, audio)
        print(f"[LYIR] Audio saved to {filepath}")
        return filepath

    def estimate_bark_syllables(filepath):
        rate, data = wav.read(filepath)
        data = data.flatten()
    
        # Normalize
        data = data / np.max(np.abs(data))
    
        # Envelope detection
        envelope = np.abs(scipy.signal.hilbert(data))
        envelope = scipy.signal.medfilt(envelope, 201)

        # Bark thresholding (basic peak detection)
        peaks, _ = scipy.signal.find_peaks(envelope, height=0.3, distance=20000)  # distance in samples

        syllable_count = len(peaks)
        print(f"[LYIR] Detected {syllable_count} bark(s) from Tucker.")
        return syllable_count

    def store_learning(word, syllables):
        if word not in dog_memory:
        dog_memory[word] = []
        dog_memory[word].append(syllables)
        with open(MEMORY_FILE, "w") as f:
        json.dump(dog_memory, f, indent=2)
        print(f"[LYIR] Learned: '{word}' → {syllables} bark(s)")

    def ask_tucker(word):
        print(f"[LYIR] Ask Tucker: How many syllables are in '{word}'?")
        filename = f"response_{int(time.time())}.wav"
        filepath = record_audio(filename)
        syllables = estimate_bark_syllables(filepath)
        store_learning(word, syllables)

    # Example use loop 
    if __name__ == "__main__":
        while True:
        user_input = input("\nAsk LYIR to analyze a word (or type 'exit'): ").strip()
        if user_input.lower() == "exit":
            break

    if __name__ == "__main__":
        lyir = Lyir()
        lyir.run()
