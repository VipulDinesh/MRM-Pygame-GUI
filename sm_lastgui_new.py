import pygame, socket, os, threading

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

manual_y_axis = 0
manual_x_axis = 0

AXIS_LEFT_STICK_X = 0
AXIS_LEFT_STICK_Y = 1
AXIS_RIGHT_STICK_X = 3
AXIS_RIGHT_STICK_Y = 2
TRIGGER_RIGHT = 5
TRIGGER_LEFT = 4
# Labels for DS4 controller buttons
# # Note that there are 14 buttons (0 to 13 for pygame, 1 to 14 for Windows setup)
BUTTON_B = 1
BUTTON_Y = 3
BUTTON_A = 0
BUTTON_X = 2
GEARUP = 5
GEARDOWN = 4
BUTTON_L2 = 7
BUTTON_R2 = 8
BUTTON_SHARE = 8
BUTTON_OPTIONS = 6

BUTTON_LEFT_STICK = 10
BUTTON_RIGHT_STICK = 11

D_PAD_UP = 13
D_PAD_DOWN = 14
LEFT_ARROW = 13
RIGHT_ARROW = 14
BUTTON_PS = 5
BUTTON_PAD = 15
GEARUP_toggle = True
GEARDOWN_toggle = True
GD = 0
GU = 0
Gear = 0
A = 0
trigger = 0
resetValue = 0
driveMode=0

# Initial Count

Gear = 0
Prev_Gear = 0

# Timestamp of the last button press in ms
interval = 10
debounce_time = 200
ping_delay = 3000

# Immediately enters loop instead of waiting first n ms
last_transmission_time= -interval
last_press_time = -debounce_time
last_ping_time= -ping_delay

ip_dict={}
ip_dict_prev={}
output_string = " M{Gear}X{left_joystick_x}Y{left_joystick_y}P{right_joystick_x}Q{right_joystick_y}A{A}S{trigger}R{resetValue}D{driveMode}E"


class TextPrint:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.Font(None, 30)

    def tprint(self, screen, text, pos):
        text_bitmap = self.font.render(text, True, pygame.Color('white'))
        screen.blit(text_bitmap, pos)
    
    def rprint(self, screen, text, start_pos, dim):
        screen.fill(pygame.Color("black"), start_pos+dim)
        self.tprint(screen, text, start_pos)

# Sets the count modifier to the os type
ping_count = '-n 1' if os.name == 'nt' else '-c 1'
timeout_count = '-w 100' if os.name == 'nt' else '-W 0.1'

def ping_device(ip_dict):
    for hostname in ip_dict:
        ip_dict_prev[hostname]=ip_dict[hostname][1]
        response = os.popen(f"ping {ip_dict[hostname][0]} {ping_count} {timeout_count}").read()
        if "Received = 1" and "Approximate" in response:
            ip_dict[hostname][1]=True
        else:
            ip_dict[hostname][1]=False

def map(value, fromLow, fromHigh, toLow, toHigh):
    # Calculate the scaled value
    scaled_value = (value - fromLow) * (toHigh - toLow) / \
        (fromHigh - fromLow) + toLow
    # Return the scaled value
    return round(scaled_value)

#create list of ips to ping
with open("ip_list.txt", "r") as file:
    for line in file:
        if line.strip()[0]=="#":
            pass
        else:
            hostname, ip_addr = line.strip().split("=")
        ip_dict[hostname]=[ip_addr, False]
    for hostname in ip_dict:
        ip_dict_prev[hostname]=ip_dict[hostname][1]
    del hostname, ip_addr, line, file

# initialisation
pygame.init() #time.get_ticks() needs whole pygame initialised - look into it
pygame.joystick.init()
controller = pygame.joystick.Joystick(0)
controller.init()
print("Joystick Successfully connected")


pygame.display.init()
screen = pygame.display.set_mode((800, 300))
pygame.display.set_caption("SM & Drive System")
text_print = TextPrint()


HOST = "10.0.0.7"
PORT = 5005
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    addr = (HOST, PORT)
    print('Sending to', addr)
    
    text_print.tprint(screen, f"Sending to {addr}", (10,10))
    
    # Static Text
    pygame.event.pump()
    #text_print.reset()
    text_print.tprint(screen, f"Y: Pitch Down", (10,50))
    text_print.tprint(screen, f"A: Pitch Up", (10,70))
    text_print.tprint(screen, f"B: Right Roll", (10,90))
    text_print.tprint(screen, f"X: Left Roll", (10,110))
    text_print.tprint(screen, f"R-Trigger: UP", (10,130))
    text_print.tprint(screen, f"L-Trigger: DOWN",(10,150))
    text_print.tprint(screen, f"R-joystick: Left-Right,Front-Back ",(10,170))
    text_print.tprint(screen, f"L-Shift: IK Stop", (10,190))
    text_print.tprint(screen, f"R-Shift: FK", (10,210))
    text_print.tprint(screen, f"Gear: 0", (10,230))
    pygame.draw.line(screen, pygame.Color("white"), (400, 0), (400, 300))
    text_print.tprint(screen, f"Pinging IP Addresses", (410,10))
    i=50
    for hostname in ip_dict:
        text_print.tprint(screen, f"{hostname}: {ip_dict[hostname][0]} - {ip_dict[hostname][1]}", (410,i))
        i+=20
    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()

    left_joystick_0 = controller.get_axis(AXIS_LEFT_STICK_X)
    left_joystick_x_0 = int(map(left_joystick_0, -1, 1, -1023-100, 1023+100))
    left_joystick_y_0 = (map(controller.get_axis(AXIS_LEFT_STICK_Y), -1, 1, -1023, 1023))
    left_joystick_y = str(left_joystick_y_0)
    right_joystick_x_0 = (map(controller.get_axis(AXIS_RIGHT_STICK_X), -1+0.1, 1-0.1, 10, -10))
    right_joystick_x = str(right_joystick_x_0)
    right_joystick_y_0 = (map(controller.get_axis(AXIS_RIGHT_STICK_Y), -1+0.1, 1-0.1, -10, 10))
    right_joystick_y = str(right_joystick_y_0)
    
    # Send data every 0.1 seconds
    running = True
    
    pygame.key.get_focused()
    
    #Update Gear value only on change
    while running:
        if Prev_Gear!=Gear:
            text_print.rprint(screen, f"{Gear}", (70,230),(12,20))
            pygame.display.flip()
            Prev_Gear=Gear

        ping_change = False
        for hostname in ip_dict:
            if ip_dict[hostname][1] != ip_dict_prev[hostname]:
                ping_change=True
                ip_dict_prev[hostname]=ip_dict[hostname][1]

        if ping_change:
            i=50
            for hostname in ip_dict:
                text_print.rprint(screen, f"{hostname}: {ip_dict[hostname][0]} - {ip_dict[hostname][1]}", (410,i),(300,20))
                i+=20
            pygame.display.flip()

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    if driveMode == 0:
                        driveMode=1
                    else:
                        driveMode=0
                elif event.key == pygame.K_RSHIFT:
                    if driveMode == 0 or driveMode == 1:
                        driveMode = 2
                    else:
                        driveMode = 0
                elif event.key == pygame.K_1:
                    A = 8
                elif event.key == pygame.K_2:
                    A = 9
                elif event.key == pygame.K_3:
                    A = 0
                elif event.key == pygame.K_DOWN:
    # Increase Y-axis value when the down arrow key is pressed
                    manual_y_axis += 0.1
                elif event.key == pygame.K_UP:
    # Decrease Y-axis value when the up arrow key is pressed
                    manual_y_axis -= 0.1
                elif event.key == pygame.K_LEFT:
    # Increase Y-axis value when the down arrow key is pressed
                    manual_x_axis += 0.1
                elif event.key == pygame.K_RIGHT:
    # Decrease Y-axis value when the up arrow key is pressed
                    manual_x_axis -= 0.1
                elif event.key == pygame.K_9:
                    resetValue = 2
                elif event.key == pygame.K_0:
                    resetValue = 0
                elif event.key == pygame.K_r:
                    A = 12
                elif event.key == pygame.K_t:
                    A = 11
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BUTTON_Y:
                    A = 1
                    print("A has been pressed")
                elif event.button == BUTTON_A:
                    print("B has been pressed")
                    A = 2
                elif event.button == BUTTON_B:
                    print("X has been pressed")
                    A = 3
                elif event.button == BUTTON_X:
                    print("Y has been pressed")
                    A = 4
            elif event.type == pygame.JOYHATMOTION:
                if event.value[0] == -1:
                    if driveMode == 0:
                        driveMode=1
                    else:
                        driveMode=0
                if event.value[1] == 1:
                    print("D_PAD_UP has been pressed")
                    A = 6
                elif event.value[1] == -1:
                    print("D_PAD_DOWN has been pressed")
                    A = 5
                elif event.value[0] == 1:
                    print("D_PAD_Right has been pressed")
                    A = 7
                # elif event.value[0] == -1:
                #     print("D_PAD_LEFT has been pressed")
                #     resetValue = 1
                elif event.value[1] == 0:
                    A = 0
                    resetValue = 0
            elif event.type == pygame.JOYBUTTONUP:
                # if event.key == pygame.K_1 or event.key == pygame.K_2:
                A = 0
        
        if pygame.time.get_ticks() - last_ping_time >= ping_delay:
            last_ping_time=pygame.time.get_ticks()
            threading.Thread(target=ping_device, daemon=True, args=(ip_dict,)).start()

        if pygame.time.get_ticks() - last_transmission_time >= interval:
            # The interval has passed, reset the timer and send data
            last_transmission_time=pygame.time.get_ticks()

            R1 = controller.get_button(GEARUP)
            L1 = controller.get_button(GEARDOWN)
            # Y=controller.get_button(BUTTON_X)
            # A=controller.get_button(BUTTON_Y)
            # B=controller.get_button(BUTTON_A)
            # X=controller.get_button(BUTTON_B)

            if R1:
                # Check for debouncing
                if pygame.time.get_ticks() - last_press_time >= debounce_time:
                    if Gear < 9:
                        Prev_Gear = Gear
                        Gear += 1
                        last_press_time = pygame.time.get_ticks()
            if L1:
                # Check for debouncing
                if pygame.time.get_ticks() - last_press_time >= debounce_time:
                    if Gear > 0:
                        Prev_Gear = Gear
                        Gear -= 1
                        last_press_time = pygame.time.get_ticks()

            pygame.event.pump()
            left_joystick_0 = controller.get_axis(AXIS_LEFT_STICK_X)
            left_joystick_x_0 = int(map(left_joystick_0 + manual_x_axis, -1, 1, -1023-100, 1023+100))
            left_joystick_x = str(left_joystick_x_0)
            left_joystick_y_0 = (map(controller.get_axis(AXIS_LEFT_STICK_Y) + manual_y_axis, -1, 1, -1023, 1023))
            left_joystick_y = str(left_joystick_y_0)
            right_joystick_x_0 = (map(controller.get_axis(AXIS_RIGHT_STICK_X), -1+0.1, 1-0.1, 10, -10))
            right_joystick_x = str(right_joystick_x_0)
            right_joystick_y_0 = (map(controller.get_axis(AXIS_RIGHT_STICK_Y), -1+0.1, 1-0.1, -10, 10))
            right_joystick_y = str(right_joystick_y_0)
            
            if int(trigger) >= 0:
                right_trigger_axis = (map(controller.get_axis(TRIGGER_RIGHT), -1, 1, 0, 10))
                trigger = str(right_trigger_axis)
            if int(trigger) <= 0:
                left_trigger_axis = (map(controller.get_axis(TRIGGER_LEFT), -1, 1, 0, -10))
                trigger = str(left_trigger_axis)
            data = output_string.format(Gear=Gear, left_joystick_x=left_joystick_x, left_joystick_y=left_joystick_y, right_joystick_x=right_joystick_x, right_joystick_y=right_joystick_y, A=A, trigger=trigger, resetValue=resetValue, driveMode=driveMode, E=0)
            print(data)
            s.sendto(data.encode(), (addr))

# To Do - if __name__ == "__main__", move main code into main() function/class
# To Do - Make display, controller and socket independent (classes?)
# To Do - Add ping as separate section
# To Do - Move from dictionary to list in pinging to maintain order
# To Do - Refresh only the true/false part of specific host which changes