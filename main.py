import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import base64
import re
import json
import mimetypes
from PIL import Image, ImageTk
import io
import cv2
import numpy as np
import os
import sys
import requests
import shutil

class DigitSumCalculator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Scan2Sum By Ankit v1.0.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#f5f5f5")
        self.center_window()
        self.setup_ui()
        self.log_queue = []
        self.typing_in_progress = False


    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
      self.canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
      self.canvas.pack(fill="both", expand=True)
      self.draw_gradient()

      frame = tk.Frame(
        self.canvas,
        bg="#ffffff",
        highlightthickness=1,  
        highlightbackground="#3498db"  
    )
      frame.place(relx=0.5, rely=0.1, anchor="n")

      tk.Label(frame, text="Scan2Sum Image Digits",
             font=("Segoe UI", 20, "bold"), bg="#ffffff", fg="#2c3e50").pack(pady=(10, 5))

      tk.Label(frame, text="Upload an image with numbers. We'll do the rest!",
             font=("Segoe UI", 12), bg="#ffffff", fg="#555555").pack(pady=(0, 10))

      self.upload_btn = ttk.Button(frame, text="📁 Upload Image", command=self.process_image)
      self.upload_btn.pack(pady=10)

      self.result_label = tk.Label(frame, text="", font=("Segoe UI", 16, "bold"),
                               bg="#ffffff", fg="#27ae60")
      self.result_label.pack()

      self.file_label = tk.Label(frame, text="", font=("Segoe UI", 10),
                             bg="#ffffff", fg="#7f8c8d")
      self.file_label.pack()

      self.status_label = tk.Label(frame, text="", font=("Segoe UI", 10),
                               bg="#ffffff", fg="#2980b9")
      self.status_label.pack()

      log_outer = tk.Frame(
    self.canvas,
    bg="#ffffff", 
    highlightthickness=1.3,
    highlightbackground="#3498db",
    relief="solid" 
)
      log_outer.place(relx=0.5, rely=0.55, anchor="n", relwidth=0.88, relheight=0.38)

      self.canvas.create_rectangle(
          70, 340, 730, 560, outline="#ccc", width=2, fill="#6edbff", tags="log_box"
    )
      self.canvas.tag_lower("log_box")

      log_frame = tk.Frame(log_outer, bg="#ffffff", bd=0)
      log_frame.pack(fill="both", expand=True, padx=10, pady=10)

      self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 10, "italic"),
                            bg="#fbfbfb", fg="#2c3e50", state="disabled",
                            borderwidth=0, relief="flat", highlightthickness=0)
      self.log_text.pack(fill="both", expand=True)

      scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
      scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
      self.log_text.config(yscrollcommand=scrollbar.set)


    def draw_gradient(self):
      """Draw a soft vertical gradient background on the canvas"""
      for i in range(0, 600):
        r = int(245 - (i * 0.1)) 
        g = int(245 - (i * 0.2))
        b = 255
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.canvas.create_line(0, i, 800, i, fill=color)


    def _log_with_typing(self, message, tag):
      """Internal function to type out log messages with color"""
      index = 0
      delay = 0.01

      def type_char():
        nonlocal index
        if index < len(message):
            char = message[index]
            self.log_text.insert("end", char)
            self.log_text.tag_add(tag, "end-2c", "end-1c")
            self.log_text.tag_config(tag, foreground=self.get_log_color(tag))
            self.log_text.see("end")
            index += 1
            self.root.after(delay, type_char)
        else:
            self.log_text.insert("end", "\n")
            self.log_text.config(state="disabled")

      type_char()


    def get_log_color(self, level):
      colors = {
        "info": "#444",
        "success": "#2e7d32",
        "error": "#b71c1c",
        "warning": "#e67e22",
        "debug": "#2980b9"
    }
      return colors.get(level, "#333")
    
    def preprocess_image_cv(image_path):
      """Preprocess image to improve OCR accuracy"""
      img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
      if img is None:
          raise ValueError("Failed to load image")
      blur = cv2.GaussianBlur(img, (5, 5), 0)
      _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
      processed_path = image_path.replace(".", "_processed.")
      cv2.imwrite(processed_path, thresh)
      return processed_path

    def process_image(self):
      """Handle image processing workflow for multiple files"""
      filetypes = [("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff"), ("All files", "*.*")]
      file_paths = filedialog.askopenfilenames(title="Select Image(s)", filetypes=filetypes)

      if not file_paths:
        return

      self.log_clear()
      total_sum = 0.0
      success_count = 0
      self.status_label.config(text="⏳ Processing images...", fg="#007acc")
      self.result_label.config(text="")  
      self.root.update()

      for file_path in file_paths:
        self.log("📁 Selected file: " + file_path.split("/")[-1], "info")
        self.file_label.config(text=f"File: {file_path.split('/')[-1]}")
        self.root.update()

        try:
            digit_sum = self.extract_with_ocr_space(file_path)
            if digit_sum is not None:
                total_sum += digit_sum
                success_count += 1
                self.log(f"✅ Sum for {file_path.split('/')[-1]}: {digit_sum}", "success")
            else:
                self.log(f"⚠️ No digits found in {file_path.split('/')[-1]}", "warning")
        except Exception as e:
            self.log(f"❌ Error processing {file_path.split('/')[-1]}: {str(e)}", "error")

      if success_count > 0:
        self.result_label.config(
            text=f"Total Sum of All Images: {round(total_sum, 2)}", fg="#2e7d32"
        )
        self.status_label.config(
            text=f"Processed {success_count} out of {len(file_paths)} image(s)", fg="#2e7d32"
        )
      else:
        self.result_label.config(text="❌ No valid results", fg="red")
        self.status_label.config(text="No valid digit sums were extracted", fg="red")


    def extract_with_ocr_space(self, image_path):
        """Extract text from image using OCR.space API"""
        image_base64 = self.image_to_base64(image_path)
        if not image_base64:
            return None

        content_type = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
        formatted_base64 = f"data:{content_type};base64,{image_base64}"

        payload = {
            "apikey": "K81247797588957",
            "language": "eng",
            "isOverlayRequired": False,
            "filetype": image_path.split('.')[-1],
            "detectOrientation": True,
            "scale": True,
            "OCREngine": 2,
            "base64Image": formatted_base64
        }

        try:
            response = requests.post(
                "https://api.ocr.space/parse/image",
                data=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.log(f"OCR Raw Response: {json.dumps(data, indent=2)}", "debug")
                
                if data["OCRExitCode"] == 1:
                    text = data["ParsedResults"][0]["ParsedText"]
                    self.log(f"Extracted Text:\n{text}", "info")
                    return self.sum_all_digits(text)
                else:
                    error_msg = data.get('ErrorMessage', 'Unknown OCR error')
                    self.log(f"❌ OCR Error: {error_msg}", "error")
                    self.suggest_image_improvements()
                    return None
            else:
                self.log(f"❌ API Error {response.status_code}: {response.text}", "error")
                return None

        except requests.exceptions.RequestException as e:
            self.log(f"❌ API request failed: {str(e)}", "error")
            return None

    def suggest_image_improvements(self):
        """Provide suggestions for better OCR results"""
        suggestions = [
            "1. Use higher contrast between text and background",
            "2. Ensure image is well-lit and in focus",
            "3. Try cropping to just the numbers",
            "4. Use a plain background if possible",
            "5. Save as PNG instead of JPG for better quality"
        ]
        self.log("💡 Try these image improvements:", "info")
        for suggestion in suggestions:
            self.log(f"   {suggestion}", "info")

    def sum_all_digits(self, text):
        """Calculate sum of all numbers found in text"""
        numbers = re.findall(r'\d+\.?\d*', text)
        if not numbers:
            self.log("No numbers found in extracted text", "warning")
            return None

        self.log(f"Extracted numbers: {numbers}", "info")

        total = 0.0
        for num in numbers:
            try:
                value = float(num)
                self.log(f"Processing: {value} (from '{num}')", "debug")
                total += value
            except ValueError:
                self.log(f"Skipping invalid number: {num}", "warning")

        self.log(f"Intermediate total: {total}", "debug")
        return round(total, 2)

    def image_to_base64(self, image_path):
        """Convert image to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.log(f"❌ Image read error: {str(e)}", "error")
            return None

    def log(self, message, level="info"):
      """Add message to log panel with typing animation"""
      self.log_queue.append((message, level))
      if not self.typing_in_progress:
        self.show_next_log()


    def show_next_log(self):
      if not self.log_queue:
        self.typing_in_progress = False
        return

      message, tag = self.log_queue.pop(0)
      self.typing_in_progress = True
      self.log_text.config(state="normal")

      index = 0
      def type_char():
        nonlocal index
        if index < len(message):
            self.log_text.insert("end", message[index])
            self.log_text.tag_add(tag, "end-2c", "end-1c")
            self.log_text.tag_config(tag, foreground=self.get_log_color(tag))
            self.log_text.see("end")
            index += 1
            self.root.after(10, type_char)
        else:
            self.log_text.insert("end", "\n")
            self.log_text.config(state="disabled")
            self.root.after(200, self.show_next_log)  
      type_char()

    def log_clear(self):
      """Clear the log panel"""
      self.log_text.config(state="normal")
      self.log_text.delete(1.0, "end")
      self.log_text.config(state="disabled")

    def show_error(self, message):
        """Display error message to user"""
        self.result_label.config(text="❌ Processing failed", fg="red")
        self.status_label.config(text=message, fg="red")
        self.log(message, "error")
        messagebox.showerror(
            "Processing Error",
            f"{message}\n\nTroubleshooting:\n"
            "1. Check your internet connection\n"
            "2. Try a different image\n"
            "3. Ensure the image is clear and upright\n"
            "4. Contact support if issue persists"
        )





def self_update():
    # GitHub raw file URL (update this link)
    UPDATE_URL = "https://github.com/yourname/yourrepo/releases/latest/download/main.py"
    
    try:
        # Download the latest version
        response = requests.get(UPDATE_URL)
        with open("main_new.py", "wb") as f:
            f.write(response.content)
        
        # Replace the old file
        if os.path.exists("main.py"):
            os.replace("main_new.py", "main.py")
            print("Update successful! Restart the app.")
            sys.exit(0)
    except Exception as e:
        print(f"Update failed: {e}")

if input("Check for updates? (y/n): ").lower() == "y":
    self_update()

if __name__ == "__main__":
    try:
        app = DigitSumCalculator()
        app.root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application error: {str(e)}")