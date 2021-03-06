import cv2
import time
import threading
import pyzbar.pyzbar as pyzbar 
from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from storage import Storage

code = ''
class KivyCamera(Image):

    def __init__(self, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)

    def start(self, mode, fps=30):
        self.store = Storage()
        self.mode = mode
        self.capture = cv2.VideoCapture(0)
        global code
        code = ''
        self.t = threading.Thread(target=self.listen_thread)
        self.t.start()
        Clock.schedule_interval(self.update, 1.0 / fps)

    def stop(self):
        try:    
            Clock.unschedule(self.update)
            Clock.unschedule(self.listening)
            self.t.join()
            self.capture.release()
        except AttributeError: 
            pass

    def update(self, dt):
        ret, frame = self.capture.read()
        try:    
            if frame.any():
                decodedObjs = self.__decode(frame)
                frame = self.__display(frame, decodedObjs)
                texture = self.texture
                w, h = frame.shape[1], frame.shape[0]
                if not texture or texture.width != w or texture.height != h:
                    self.texture = texture = Texture.create(size=(w, h))
                    texture.flip_vertical()
                texture.blit_buffer(frame.tobytes(), colorfmt='bgr')
                self.canvas.ask_update()
            
        except (AttributeError, SyntaxError) as e:
            self.capture = cv2.VideoCapture(0)
            
            
    def __decode(self, im): 
        # Find barcodes and QR codes
        decodedObjects = pyzbar.decode(im)
        # Print results
        for obj in decodedObjects:
            global code
            code = obj.data.decode("utf-8")
            print(code)
        return decodedObjects
  
    # Display barcode and QR code location  
    def __display(self, im, decodedObjects):
        for decodedObject in decodedObjects: 
          points = decodedObject.polygon  
          if len(points) == 4 : 
            cv2.rectangle(im, (points[0].x, points[0].y), (points[2].x, points[2].y), (0,255,0), 3)
        cv2.rectangle(im, (100, 380), (550, 100), (255,255,255), 8)
        return im
            
    def listening(self, dt):
        print('listening')
        try:
            global code 
            if (code and self.mode=="load"):
                if self.store.load_parcel(code):
                    self.t.join()
                    self.parent.parent.exit_scan()
                # import pdb; pdb.set_trace()
                code = ""
                
            elif (code and self.mode=="unlock"):
                if self.store.unlock_parcel(code):
                    self.t.join()
                    self.parent.parent.exit_scan()

        except ValueError as e:
            Clock.unschedule(self.listening)
            box = FloatLayout()
            box.add_widget(Label(text="""Something went wrong with the server.
                    \nThe parcel failed to load into the robot.""", font_size=17,
                    pos_hint={'center_x': 0.5, 'center_y': 0.7},
                    color=(0,0,0,1)))
            button = RoundedButton(text="Try again!",
                    pos_hint={'center_x': 0.5, 'center_y': 0.4},
                    size_hint=(0.5, 0.2), 
                    color=(0,0,0,1))
            button.bind(on_press=lambda *args: self.restart_listening(popup))
            box.add_widget(button)
            popup = Popup(title="Error",
                    content=box,
                    size_hint=(None, None), size=(400, 400))
            popup.open()
            print("caught error, ", e.args)
       
    def restart_listening(self, popup):
        global code
        code = ''
        popup.dismiss()
        Clock.schedule_interval(self.listening, 1)

    def listen_thread(self, **kwargs):
        print("listen thread called")
        Clock.schedule_interval(self.listening, 1)
            

class RoundedButton(Button):
    pass
    
