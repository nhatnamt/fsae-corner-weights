import os
import sys

import serial
from nicegui import app, run, ui
from serial.tools import list_ports

from cog_viewer import CogViewer


# Function to list available serial ports
def get_available_ports():
    return [port.device for port in list_ports.comports()]


# ---------------------------------------------------------------------------- #
#                                 UI Components                                #
# ---------------------------------------------------------------------------- #


class WeightDisplay:

    def __init__(self, label, weight):
        self.label = label
        self.weight = weight
        with ui.column().classes('w-full p-4 border border-gray-300 border-2 rounded-md flex') as self.container:
            ui.label(self.label).classes('text-4xl font-medium text-gray-600	')
            self.weight_label = ui.label(f'{self.weight} kg').classes(
                'w-full text-8xl grow py-auto flex justify-center items-center text-gray-700')

    def set_weight(self, weight):
        self.weight = self.remove_newline(weight)
        self.weight_label.set_text(f'{self.weight} kg')

    def remove_newline(self, data):
        return data.replace('\n', '').replace('\r', '')


class RatioDisplay:

    def __init__(self, label, ratio='0.0/0.0'):
        self.label = label
        self.ratio = ratio
        with ui.column().classes('w-full').classes('p-4 border border-gray-300 border-2	rounded-md flex'):
            ui.label(self.label).classes('text-3xl font-medium text-gray-600')
            self.ratio_label = ui.label(ratio).classes(
                'w-full text-5xl grow py-auto flex justify-center items-center text-gray-700')

    def set_ratio(self, ratio):
        self.ratio = self.remove_newline(ratio)
        self.ratio_label.set_text(ratio)

    def remove_newline(self, data):
        return data.replace('\n', '').replace('\r', '')


def refresh_ports():
    selected_port.set_options(get_available_ports())


ports = get_available_ports()
baudrates = [9600, 19200, 38400, 57600, 115200]  # List of common baud rates

raw_data_cache = []  # Cache for raw data
ui.colors(primary='#1976d2')
ui.query('.q-page').classes('flex w-full')
ui.query('.nicegui-content').classes('grow no-wrap justify-stretch')
with ui.grid(columns='2fr 5fr').classes('w-full grow'):
    with ui.column().classes('w-full flex'):
        total_weight = WeightDisplay('Total Weight', 0)
        total_weight.container.classes('flex-auto')
        with ui.grid(columns='1fr 1fr').classes('w-full flex-auto'):
            left_right_ratio = RatioDisplay('Left/Right Ratio')
            front_rear_ratio = RatioDisplay('Front/Rear Ratio')
        with ui.row().classes('w-full p-4 border border-gray-300 border-2 rounded-md flex-none'):
            ui.label('Settings').classes('text-3xl font-medium text-gray-600')
            with ui.grid(columns='1fr 1fr').classes('w-full'):
                selected_port = ui.select(ports, label='Select Port').on('focus', refresh_ports)
                if ports:
                    selected_port.set_value(ports[0])
                selected_baudrate = ui.select(baudrates, label='Select Baudrate', value=115200)
            with ui.grid(columns='1fr 1fr').classes('w-full'):
                connect_button = ui.button('Connect').classes('w-full').props('outline')
                disconnect_button = ui.button('Disconnect').classes('w-full').props('flat')
            log = ui.log().style('white-space: normal')  # Log for raw data
            show_log = ui.checkbox('Show Log')

    taring_dlg = ui.dialog().classes('w-full').props('max-width sm')
    with taring_dlg, ui.card():
        ui.label('Taring the scale').classes('text-3xl font-medium text-gray-600 w-full')
        with ui.row().classes('w-full flex justify-center items-center'):
            ui.label('Please wait for the scale to tare   ').classes('text-2xl font-medium text-gray-600')
            ui.spinner('dots', size='lg', color='red')

    with ui.grid(columns='1fr 1fr 1fr').classes('w-full'):
        with ui.column().classes('w-full flex'):
            fl = WeightDisplay('FL', 0)
            fl.container.classes('flex-auto')
            rl = WeightDisplay('RL', 0)
            rl.container.classes('flex-auto')
        cogViewer = CogViewer().classes('w-full p-4 border border-gray-300 border-2 rounded-md')
        with ui.column().classes('w-full flex'):
            fr = WeightDisplay('FR', 0)
            fr.container.classes('flex-auto')
            rr = WeightDisplay('RR', 0)
            rr.container.classes('flex-auto')


def handle_data(data):
    if show_log.value:
        log.push(data)  # Show verbose data


# Function to restore cached data when verbose is re-enabled
def toggle_log_verbose(checked):
    if checked:
        log.set_text('\n'.join(raw_data_cache))  # Restore cached data


show_log.on('change', lambda e: toggle_log_verbose(e.value))
port = None  # Placeholder for the serial port connection


def remove_newline(data):
    return data.replace('\n', '').replace('\r', '')


# Function to parse the serial data
def parse_serial_data(data):
    result = remove_newline(data).split(':')
    if result[0] == 'Car total weight (kg)':
        total_weight.set_weight(result[1])
    elif result[0] == 'FR':
        parts = remove_newline(data).split()
        fr.set_weight(parts[1])
        fl.set_weight(parts[3])
        rr.set_weight(parts[5])
        rl.set_weight(parts[7])
    elif result[0] == 'Front/Rear ratio':
        f2r_ratio = result[1].split()[0]
        l2r_ratio = result[2]
        f_ratio = float(f2r_ratio.split('/')[0])
        l_ratio = float(l2r_ratio.split('/')[0])
        left_right_ratio.set_ratio(l2r_ratio)
        front_rear_ratio.set_ratio(f2r_ratio)
        cogViewer.update_cog((1 - f_ratio), (1 - l_ratio))
    elif result[0] == "Taring":
        taring_dlg.open()
    elif result[0] == "Done":
        taring_dlg.close()


# Asynchronous function to read from the serial port and parse data
async def read_loop() -> None:
    while not app.is_stopped:
        try:
            line = await run.io_bound(port.readline)
            if line:
                decoded_line = line.decode()
                handle_data(decoded_line)
                parse_serial_data(decoded_line)
                # parsed_output.set_text(parsed_data)  # Display parsed data
        except Exception as e:
            log.push(f"Error reading from serial port {e}")
            break


# Connect button event handler
async def handle_click():
    global port
    if port is None or not port.is_open:
        try:
            port = serial.Serial(selected_port.value, baudrate=selected_baudrate.value, timeout=0.1)
            log.push(f'Connected to {selected_port.value} at {selected_baudrate.value} baudrate.')
            # Start the read loop asynchronously
            await read_loop()
        except Exception as e:
            log.push(f"Failed to open serial port: {e}")
    else:
        log.push(f"Already connected to {selected_port.value}")


connect_button.on('click', handle_click)
disconnect_button.on('click', lambda: port and port.close())

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

assets = os.path.join(os.path.dirname(__file__), 'assets')
app.add_static_files('/assets', assets)
app.on_shutdown(lambda: port and port.close())
app.native.window_args['maximized'] = True
app.native.window_args['resizable'] = False
ui.run(title='Corner View V1', reload=False, native=True)
# ui.run(title='Corner View V1', port=7000)
