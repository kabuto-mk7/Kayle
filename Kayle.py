from reportlab.pdfbase.pdfmetrics import stringWidth
from tkinter import filedialog
from ttkthemes import *
import tkinter as tk
from reportlab.pdfgen.canvas import Canvas
import soundfile as sf
import sys
import threading
import joblib
import os
import datetime
import speech_recognition as sr

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="#222", padx=50, pady=50)
        self.master.wm_minsize(900, 300)
        self.master = master
        self.master.title("KAYLE")
        self.master.geometry("500x300")
        self.master.configure(bg="#222")
        self.pack(fill="both", expand=True)

        # Create a separate frame for the terminal
        self.terminal_frame = tk.Frame(self, bg="#222", padx=10, pady=10)
        self.terminal_frame.pack(side="right", fill="both", expand=True)

        # Create the terminal text widget inside the frame
        self.output_text = tk.Text(self.terminal_frame, bg="#222", fg="white", font=("Courier New", 10))
        self.output_text.pack(side="left", fill="both", expand=True)

        # Add other GUI elements here

        self.create_widgets()
        self.round_corners()

    class HatespeechClassifier:
        def __init__(self, model_path='D:/ClipMaker/best_regression_model.joblib'):
            self.model = joblib.load(model_path)

        def classify(self, text):
            score = self.model.predict([text])[0]
            if score < -1:
                label = "Strong Counter-Speech"
            elif -1 <= score < -0.5:
                label = "Counter-Speech"
            elif -0.5 <= score < 0:
                label = "Unlikely Hateful"
            elif 0 <= score < 0.5:
                label = "Likely Hateful"
            else:
                label = "Strong Hateful"
            return score, label

    def gen_report(self, path, transcript, classification):
        name = os.path.splitext(path)[0] + '_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S' + '.pdf')
        canvas = Canvas(name, pagesize=(612.0, 792.0))
        text = canvas.beginText(50, 700)
        text.setFont("Times-Roman", 12)
        text.textLine("File Name: " + str(os.path.basename(path)))
        text.textLine("Date of Classification: " + str(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))

        # split the transcript into multiple lines based on available space on the page
        lines = transcript.split('\n')
        num_lines = len(lines)
        y_start = 600  # starting y position
        line_height = 15  # height of each line
        for i, line in enumerate(lines):
            words = line.split()
            for word in words:
                x, y = text.getCursor()
                if x + stringWidth(word, "Times-Roman",
                                   12) > 550:  # if the word is about to go outside the page, start a new line
                    y = y_start - i * line_height
                    if y < 50:  # if the text is about to go outside the page, start a new page
                        canvas.drawText(text)
                        canvas.showPage()
                        text = canvas.beginText(50, 700)
                        y_start = 600
                    else:
                        text.textLine("")  # start a new line
                text.textOut(word + " ")
            text.textLine("")

        text.textLine("Classification: " + str(classification))
        canvas.drawText(text)
        canvas.save()

    def redirect_output(self):
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, string):
                self.text_widget.insert("end", string)
                self.text_widget.see("end")

        sys.stdout = StdoutRedirector(self.output_text)

    def process_audio_file(self, filepath):
        # Check if the file is an audio file
        if not filepath.lower().endswith(('.wav', '.mp3', '.ogg', '.flac', '.aac')):
            return "Error: Please select an audio file."

        # Create a folder with the same name as the original file
        foldername = os.path.splitext(os.path.basename(filepath))[0]
        os.makedirs(foldername, exist_ok=True)

        # Step 2: Convert the file to a wav if necessary
        if not filepath.endswith('.wav'):
            new_filepath = os.path.join(foldername, 'temp.wav')
            data, samplerate = sf.read(filepath)
            sf.write(new_filepath, data, samplerate, subtype='PCM_16')
            filepath = new_filepath

        # Step 4: Call the transcribe_audio function on the audio file
        r = sr.Recognizer()
        with sr.AudioFile(filepath) as source:
            audio = r.record(source)

        transcript = r.recognize_google(audio)

        print(transcript)
        hc = self.HatespeechClassifier()
        score, label = hc.classify(transcript)
        print(f'Hatespeech classification: score={score}, label={label}')
        self.gen_report(filepath, transcript, label)
        return transcript

    def create_widgets(self):

        self.logo_container = tk.Frame(self, bg="#222")
        self.logo_container.pack(side="top", pady=(20, 10))
        threading.Thread(target=self.redirect_output()).start()

        self.logo_circle = tk.Canvas(
            self.logo_container,
            bg="#222",
            width=20,
            height=20,
            highlightthickness=0,
        )
        self.logo_circle.pack(side="left")
        self.logo_circle.create_oval(
            2, 2, 18, 18, fill="red", outline="red"
        )

        self.title_label = tk.Label(
            self.logo_container, text="KAYLE", font=("W95FA", 20), bg="#222", fg="white"
        )
        self.title_label.pack(side="left", padx=(5, 0))

        self.drag_label = tk.Label(
            self,
            text="Upload",
            font=("W95FA", 12),
            bg="#222",
            fg="white",
            padx=10,
            pady=10,
            relief="groove",
            bd=2,
            width=30,
            height=5,
        )
        self.drag_label.pack(pady=20)

        self.drag_label.bind("<Button-1>", self.on_drag_start)
        self.drag_label.bind("<B1-Motion>", self.on_drag_motion)
        self.drag_label.bind("<ButtonRelease-1>", self.on_drag_release)

        self.drag_label.bind("<Button-1>", self.on_drag_start)
        self.drag_label.bind("<B1-Motion>", self.on_drag_motion)
        self.drag_label.bind("<ButtonRelease-1>", self.on_drag_release)
    def on_drag_start(self, event):
        self.drag_label.config(bg="#333")

    def on_drag_motion(self, event):
        pass

    def on_drag_release(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav;*.mp3")])
        print(f"File path: {file_path}")
        self.process_audio_file(file_path)


    def round_corners(self):
        self.master.overrideredirect(1)
        self.master.geometry("+50+50")
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        self.master.geometry(f"{width}x{height}+{x}+{y}")
        self.master.bind(
            "<Map>",
            lambda event: self.master.overrideredirect(0),
        )
        self.master.bind(
            "<Unmap>",
            lambda event: self.master.overrideredirect(1),
        )

        style = ThemedStyle(self.master)
        style.theme_use("black")



if __name__ == "__main__":

    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()