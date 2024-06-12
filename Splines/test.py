import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.colorchooser import askcolor
import pandas as pd
import random
from PIL import Image, ImageTk

# Initial Configuration
pygame.init()
width, height = 1080, 720
screen = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
pygame.display.set_caption("Spline Curves - Bézier and B-spline")
gluOrtho2D(0, width, 0, height)

# Font initialization
pygame.font.init()
font = pygame.font.SysFont('Helvetica', 18)

# Control points and curves
control_points = []
curves = []
    
# Current color
current_color = [1.0, 0.0, 0.0]  # Red by default
background_color = [0.0, 0.0, 0.0, 0.0]  # Black by default

def draw_points(points):
    glPointSize(5)
    glColor3f(1.0, 1.0, 1.0)  # White for control points
    glBegin(GL_POINTS)
    for point in points:
        glVertex2f(point[0], point[1])
    glEnd()

def bezier_curve(points, t):
    n = len(points) - 1
    points = np.array(points)
    p = np.zeros(2)
    for i in range(n + 1):
        bernstein = np.math.comb(n, i) * (t**i) * ((1 - t)**(n - i))
        p += points[i] * bernstein
    return p

def points_bezier_curve(points, t):
    p = []
    for i in range(101):
        t_i = i / 100.0
        if t_i <= t:
            point = bezier_curve(points, t_i)
            p.append(point)
    return p

def cubic_spline_interpolation(points, t):
    points = np.array(points)
    n = len(points)
    k = int(t * (n - 1))
    t_i = t * (n - 1) - k
    p0 = points[k]
    p1 = points[(k + 1) % n]
    p2 = points[(k + 2) % n]
    p3 = points[(k + 3) % n]
    
    a = -0.5 * p0 + 1.5 * p1 - 1.5 * p2 + 0.5 * p3
    b = p0 - 2.5 * p1 + 2 * p2 - 0.5 * p3
    c = -0.5 * p0 + 0.5 * p2
    d = p1
    
    return a * (t_i**3) + b * (t_i**2) + c * t_i + d

def points_cubic_spline(points, t):
    p = []
    for i in range(101):
        t_i = i / 100.0
        if t_i <= t:
            point = cubic_spline_interpolation(points, t_i)
            p.append(point)
    return p
        
def draw_curves(curves):
    for curve in curves:
        color, points, bg_color = curve['color'], curve['points'], curve.get('bg_color', [0.0, 0.0, 0.0, 0.0])
        if bg_color[3] > 0:  # If the background is transparent
            glColor4f(*bg_color)
            glBegin(GL_POLYGON)
            for point in points:
                glVertex2f(point[0], point[1])
            glEnd()
        glColor3f(*color)
        glBegin(GL_LINE_STRIP)
        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()

def draw_current_curve(points, t, color, bg_color):
    if len(points) > 1:
        if mode == 'Bézier':
            curve_points = points_bezier_curve(points, t)
        elif mode == 'B-spline':
            curve_points = points_cubic_spline(points, t)
        if bg_color[3] > 0:  # If the background is transparent
            glColor4f(*bg_color)
            glBegin(GL_POLYGON)
            for point in curve_points:
                glVertex2f(point[0], point[1])
            glEnd()
        glColor3f(*color)
        glBegin(GL_LINE_STRIP)
        
        for point in curve_points:
            glVertex2f(point[0], point[1])
        glEnd()

# Functions for the current mode
mode = None

def set_bezier():
    global mode
    mode = 'Bézier'
    label2.config(text="Current mode: " + mode)
    print("Bézier mode selected.")

def set_b_spline():
    global mode
    mode = 'B-spline'
    label2.config(text="Current mode: " + mode)
    print("B-spline mode selected.")

def reset():
    global control_points, curves, mode
    control_points = []
    curves = []
    mode = None
    label2.config(text="Current mode: " + "None")
    update_points_listbox()
    print("Reset completed.")

def warning():
    messagebox.showwarning("Warning", "Select a drawing mode!")

def save_points():
    if not control_points:
        messagebox.showinfo("Information", "No points to save!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'w') as file:
            for point in control_points:
                file.write(f"{point[0]},{point[1]}\n")
        messagebox.showinfo("Success", "Points saved!")

def load_points():

    if mode is None:
        warning()
        return

    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'r') as file:
            points = []
            for line in file:
                x, y = map(float, line.strip().split(','))
                points.append([x, y])
        if points:
            global control_points
            control_points = points
            update_points_listbox()
            print("Points loaded.")
        else:
            messagebox.showinfo("Information", "File contains invalid points!")

def choose_color():
    global current_color
    color = askcolor()[0]
    if color:
        current_color = [c / 255.0 for c in color]  # Converting to normalized format for OpenGL

def choose_background_color():
    global background_color
    color = askcolor()[1]
    if color:
        bg_color = list(int(color[i:i+2], 16) for i in (1, 3, 5))
        bg_color.append(255)  # Alpha channel
        background_color = [c / 255.0 for c in bg_color]

def update_points_listbox():
    points_listbox.delete(0, tk.END)
    for point in control_points:
        points_listbox.insert(tk.END, f"x={point[0]}, y={point[1]}")

def finalize_curve():
    global background_color
    if len(control_points) > 1 and mode is not None:
        if mode == 'Bézier':
            curve_points = points_bezier_curve(control_points, t=1)
        elif mode == 'B-spline':
            curve_points = points_cubic_spline(control_points, t=1)
        curves.append({'points': curve_points, 'color': current_color, 'bg_color': background_color})
        
        control_points.clear()
        update_points_listbox()
        background_color = [0.0, 0.0, 0.0, 0.0]  # Reset the background color

animate = False
animation_speed = 0.0009
animation_t = 1
loop = False
paused = False

def animate_curves():
    global animation_t
    global loop
    if animate:
        '''
        if len(control_points) < 2:
            animate_flag()
            messagebox.showwarning("Warning", "No curve to animate!")
            return
        '''

        if paused is False:
            animation_t += animation_speed
        update_animation_progress(animation_t)

        if animation_t >= 1.0:
            if loop is False: animation_t = 1.0
            else: animation_t = 0.0
            
def loop_flag():
    global loop
    if loop is False:
        loop = True
        loop_button.config(text="On")
    else:
        loop = False
        loop_button.config(text="Off")

def pause_flag():
    global paused
    if paused is False:
        paused = True
        pause_button.config(text="On")
    else:
        paused = False
        pause_button.config(text="Off")

def animate_flag():
    global animate
    global animation_t
    if animate is False:
        animation_t = 0
        animate = True
        animation_button.config(text="Animate: On")
        animation_button2.config(text="On")

    else:
        animation_t = 1
        animate = False
        animation_button.config(text="Animate: Off")
        animation_button2.config(text="Off")
        update_animation_progress(0)

def save_curves_to_csv():
    if len(curves) == 0:
        messagebox.showwarning("Warning", "No curves finalized!")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        data = []
        for curve in curves:
            points = ','.join([f"{p[0]} {p[1]}" for p in curve['points']])
            color = ' '.join(map(str, curve['color']))
            bg_color = ' '.join(map(str, curve['bg_color']))
            data.append([mode, points, color, bg_color])
        df = pd.DataFrame(data, columns=['type', 'points', 'color', 'bg_color'])
        df.to_csv(file_path, index=False)
        messagebox.showinfo("Success", "Figure saved!")

def load_curves_from_csv():
    file_path = filedialog.askopenfilename(defaultextension=".csv",
                                           filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        reset()
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            points = [[float(point.split(' ')[0]), float(point.split(' ')[1])] for point in row['points'].split(',') if len(point.split()) == 2]
            color = list(map(float, row['color'].split()))
            bg_color = list(map(float, row['bg_color'].split()))
            curves.append({'points': points, 'color': color, 'bg_color': bg_color})
        messagebox.showinfo("Success", "Figure loaded!")

def undo():
    if len(control_points) == 0: 
        if len(curves) !=0 : curves.pop()
    else: 
        control_points.pop()
        update_points_listbox()

def draw_random_curve():
    n = random.randint(2, 10)

    control_points.clear()
    update_points_listbox()

    for _ in range(n):
        x = random.randint(50, width-50)
        y = random.randint(50, height-50)
        control_points.append([x, y])
        update_points_listbox()

    m = random.randint(0, 1)

    if m == 0: set_bezier()
    else: set_b_spline()

def on_destroy(event):
    if event.widget == root:
        print("Root window was distroyed!")
        pygame.quit()

def do_nothing():
    pass

# Tkinter interface configuration
root = tk.Tk()
root.title("Control Panel")
root.geometry("280x875")
root.configure(bg="#3A3B3C")
root.protocol("WM_DELETE_WINDOW", do_nothing)
#root.bind("<Destroy>", on_destroy)

menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=False)

file_menu.add_command(label="Undo", command = undo)
file_menu.add_command(label="Save", command = save_curves_to_csv)
file_menu.add_command(label="Load", command = load_curves_from_csv)

menubar.insert_cascade(0, label="File", menu=file_menu)

label2 = tk.Label(root, text="Current Mode: " + ("None" if mode is None else mode), fg="#C4FE00", bg="#3A3B3C", font=("Helvetica", 18, "bold"))
label2.pack(pady=20)

style_frame = ttk.Style()
style_frame.theme_use('alt')
style_frame.configure("new.TFrame", background="#000000")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

main_frame = ttk.Frame(notebook, style="new.TFrame")
main_frame.pack(fill='both', expand=True)
notebook.add(main_frame, text='Panel')

animate_frame = ttk.Frame(notebook, style="new.TFrame")
animate_frame.pack(fill='both', expand=True)
notebook.add(animate_frame, text='Animation Settings')

points_frame = ttk.Frame(notebook, style="new.TFrame")
points_frame.pack(fill='both', expand=True)
notebook.add(points_frame, text='Points')

style = ttk.Style()
style.theme_use('alt')

style.configure('TButton2.TButton', background="#080B2D", foreground="#E80822", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton2.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton3.TButton', background="#080B2D", foreground="#A313E2", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton3.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton4.TButton', background="#080B2D", foreground="#ADE213", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton4.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton5.TButton', background="#080B2D", foreground="#0093FF", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton5.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton6.TButton', background="#080B2D", foreground="#FF8F00", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton6.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton7.TButton', background="#080B2D", foreground="#00D8FF", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton7.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton8.TButton', background="#080B2D", foreground="#00FF2A", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton8.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton9.TButton', background="#080B2D", foreground="#FF00F3", font=("Helvetica", 12, "bold"), width = 18, borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton9.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton10.TButton', background="#080B2D", foreground="#FF00F3", font=("Helvetica", 12, "bold"), borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton10.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

style.configure('TButton11.TButton', background="#080B2D", foreground="#FBFF01", font=("Helvetica", 12, "bold"), borderwidth=1, focusthickness=3, focuscolor='none')
style.map('TButton11.TButton', 
          background=[('active', 'purple')],
          foreground=[('active', 'white')])

def photo(path, dim=(30, 30)):
    image_path = path  
    image = Image.open(image_path)
    image = image.resize(dim, Image.LANCZOS) 
    photo = ImageTk.PhotoImage(image)
    return photo

photo_reset = photo("reset_image.png")
photo_color_line = photo("color_line_image.jpeg")
photo_color_bg = photo("color_bg_image.jpeg")
photo_finalize_curve = photo("finalizeaza_image.png")
photo_random_curve = photo("random_image.jpeg")
photo_animate = photo("animate_image.png")
photo_save = photo("save_image.jpeg")
photo_load = photo("load_image.jpeg")
photo_undo = photo("undo_image.png")
photo_playback = photo("playback_image.jpeg", dim=(75, 75))
photo_playback_color = photo("playback_color_image.jpeg", dim=(75, 75))
photo_reset_animation = photo("reset_image1.png", dim=(30, 20))

bezier_button = ttk.Button(main_frame, text="Bézier", command=set_bezier, style="TButton2.TButton")
bezier_button.pack(pady=10)

b_spline_button = ttk.Button(main_frame, text="B-spline", command=set_b_spline, style="TButton2.TButton")
b_spline_button.pack(pady=10)

color_button = ttk.Button(main_frame, text="Curve Color", image=photo_color_line, compound=tk.RIGHT, command=choose_color, style="TButton3.TButton")
color_button.pack(pady=10)

background_button = ttk.Button(main_frame, text="Background Color", image=photo_color_bg, compound=tk.RIGHT, command=choose_background_color, style="TButton3.TButton")
background_button.pack(pady=10)

animation_button = ttk.Button(main_frame, text="Animate mode: Off", image=photo_animate, compound=tk.RIGHT, command=animate_flag, style="TButton7.TButton")
animation_button.pack(pady=10)

finalize_button = ttk.Button(main_frame, text="Finalize Curve", image=photo_finalize_curve, compound=tk.RIGHT, command=finalize_curve, style="TButton8.TButton")
finalize_button.pack(pady=10)

draw_random_curve_button = ttk.Button(main_frame, text="Random Curve", image=photo_random_curve, compound=tk.RIGHT, command=draw_random_curve, style="TButton9.TButton")
draw_random_curve_button.pack(pady=10)

undo_last_curve_button = ttk.Button(main_frame, text="Undo", image=photo_undo, compound=tk.RIGHT, command=undo, style="TButton6.TButton")
undo_last_curve_button.pack(pady=10)

reset_button = ttk.Button(main_frame, text="Reset", image=photo_reset, compound=tk.RIGHT, command=reset, style="TButton6.TButton")
reset_button.pack(pady=10)

save_button = ttk.Button(main_frame, text="Save Points", image=photo_save, compound=tk.RIGHT, command=save_points, style="TButton4.TButton")
save_button.pack(pady=10)

load_button = ttk.Button(main_frame, text="Load Points", image=photo_load, compound=tk.RIGHT, command=load_points, style="TButton4.TButton")
load_button.pack(pady=10)

save_curves_button = ttk.Button(main_frame, text="Save Figure", image=photo_save, compound=tk.RIGHT, command=save_curves_to_csv, style="TButton5.TButton")
save_curves_button.pack(pady=10)

load_curves_button = ttk.Button(main_frame, text="Load Figure", image=photo_load, compound=tk.RIGHT, command=load_curves_from_csv, style="TButton5.TButton")
load_curves_button.pack(pady=10)

label_developed_by = tk.Label(main_frame, text="Developed by Andrei, George, Nicolas", bg="#3e4149", fg="#ffffff")
label_developed_by.pack(side=tk.BOTTOM, pady=(20, 10))

points_listbox = tk.Listbox(points_frame, bg="#000000", fg="#FE00FA", font=("Helvetica", 16, "bold"))
points_listbox.pack(expand=True, fill='both')

style = ttk.Style()
style.theme_use('alt')
style.configure('Tall.Horizontal.TProgressbar',
                troughcolor='#FF019F',
                background='green',      
                thickness=30)

time_label = tk.Label(animate_frame, text="Time", fg="#FFA201", bg="#080B2D", font=("Helvetica", 16, "bold"))
time_label.grid(row=0, column=0, padx=5, pady=20, sticky="w")

speed_label = tk.Label(animate_frame, text="Speed", fg="#FFA201", bg="#080B2D", font=("Helvetica", 16, "bold"))
speed_label.grid(row=1, column=0, padx=5, pady=20, sticky="w")

animate_progress_bar = ttk.Progressbar(animate_frame, orient="horizontal", length=175, mode="determinate", style='Tall.Horizontal.TProgressbar')
animate_progress_bar.grid(row=0, column=1, padx=10, pady=20, sticky="ew")

animate_progress_bar["maximum"] = 1.0
animate_progress_bar["value"] = 0.0 

def update_animation_progress(value):
    animate_progress_bar["value"] = value

def on_click(event):
    if event.widget == animate_progress_bar and animate is True:
        click_x = event.x
        global animation_t
        animation_t = click_x / animate_progress_bar.winfo_width()

animate_progress_bar.bind("<Button-1>", on_click)
animate_progress_bar.bind("<B1-Motion>", on_click)

def speed_modified(speed):
    global animation_speed
    animation_speed = int(speed) / 10000

scale = tk.Scale(animate_frame, from_=1, to=200, orient="horizontal", background="#FF019F", foreground = "#01FF01",troughcolor='green',
                 highlightbackground='lightblue', sliderrelief=tk.RAISED, command=speed_modified)
scale.grid(row=1, column=1, padx=10, pady=20, sticky="ew")
scale.set(50)
speed_modified(50)

animate_label = tk.Label(animate_frame, text="Mode", fg="#FF00F3", bg="#080B2D", font=("Helvetica", 16, "bold"))
animate_label.grid(row=2, column=0, padx=5, pady=20, sticky="w")

animation_button2 = ttk.Button(animate_frame, text="Off", command=animate_flag, style="TButton10.TButton")
animation_button2.grid(row=2, column=1, padx=10, pady=20, sticky="ew")

loop_label = tk.Label(animate_frame, text="Loop", fg="#FBFF01", bg="#080B2D", font=("Helvetica", 16, "bold"))
loop_label.grid(row=3, column=0, padx=5, pady=20, sticky="w")

loop_button = ttk.Button(animate_frame, text="Off", command=loop_flag, style="TButton11.TButton")
loop_button.grid(row=3, column=1, padx=10, pady=20, sticky="ew")

pause_label = tk.Label(animate_frame, text="Pause", fg="#FBFF01", bg="#080B2D", font=("Helvetica", 16, "bold"))
pause_label.grid(row=4, column=0, padx=5, pady=20, sticky="w")

pause_button = ttk.Button(animate_frame, text="Off", command=pause_flag, style="TButton11.TButton")
pause_button.grid(row=4, column=1, padx=10, pady=20, sticky="ew")

reset_label = tk.Label(animate_frame, text="Reset", fg="#FBFF01", bg="#080B2D", font=("Helvetica", 16, "bold"))
reset_label.grid(row=5, column=0, padx=5, pady=20, sticky="w")

def reset_animation():
    global animation_t
    animation_t = 0
    update_animation_progress(animation_t)

reset_button2 = ttk.Button(animate_frame, image=photo_reset_animation, command = reset_animation, style="TButton11.TButton")
reset_button2.grid(row=5, column=1, padx=10, pady=20, sticky="ew")

animate_image1 = tk.Label(animate_frame, image = photo_playback)
animate_image1.grid(row=6, column=0, padx=5, pady=20)

animate_image2 = tk.Label(animate_frame, image = photo_playback_color)
animate_image2.grid(row=6, column=1, padx=5, pady=20)

# Mainloop for Pygame and Tkinter
running = True
clock = pygame.time.Clock()

def mainloop():
    global running
    while running:
        pygame.init()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if mode is None:
                    warning()
                else:
                    x, y = event.pos
                    y = height - y  # OpenGL has its origin at the bottom-left corner
                    control_points.append([x, y])
                    update_points_listbox()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    control_points.clear()
                    update_points_listbox()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_z] and keys[pygame.K_LCTRL]:
            undo()

        glClear(GL_COLOR_BUFFER_BIT)
        draw_points(control_points)
        draw_curves(curves)
        draw_current_curve(control_points, animation_t, current_color, background_color)

        if animate is True: animate_curves()
        
        pygame.display.flip()
        clock.tick(60)
        root.update_idletasks()
        root.update()

    root.destroy()
    pygame.quit()

# Starting the main loop
mainloop()
