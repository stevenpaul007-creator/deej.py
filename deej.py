import asyncio
import serial_asyncio
import pulsectl
from pulsectl import PulseVolumeInfo


# reverse sliders. 1023 to 0
reversed = True

# Initialize PulseAudio control
pulse = pulsectl.Pulse('audio-control')

# Mapping of slider indexes to target application names.
# Slider 0 controls the master volume; sliders 1-4 control specific apps.
# For slider 4, you can list multiple applications as a list.
slider_mapping = {
    1: ["Google Chrome", "Firefox"],                         # broswers
    2: ["spotify","PipeWire ALSA [mpg123]","vlc","mpv"],     # players
    3: [                                                     # games
        "World of Warcraft", 
        "Red Dead Redemption 2", 
        "Red Dead Redemption", 
        "FMOD Ex App", 
        "Civ6", 
        "Stardew Valley", 
        "Factorio: Space Age 2.0.42", 
        "Diablo IV", 
        "Gears 5", 
        "Overwatch", 
        "Balatro.exe",
        "Stardew Valley"
        ]
}

class SerialReaderProtocol(asyncio.Protocol):
    def __init__(self, pulse):
        self.pulse = pulse
        self.buffer = b""
        self.last_values = None
        self.connection_lost_future = asyncio.get_running_loop().create_future()

    def connection_made(self, transport):
        self.transport = transport
        print("Serial connection opened. Connected successfully!")

    def data_received(self, data):
        self.buffer += data
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            try:
                decoded_line = line.decode('utf-8').strip()
            except UnicodeDecodeError as e:
                continue
            self.process_line(decoded_line)

    def process_line(self, line):
        # print(line);
        # Expected format: "1023|1023|1023|1023"
        parts = line.split('|')
        if len(parts) != len(slider_mapping) + 1:
            return

        try:
            slider_values = [int(val) for val in parts]
        except ValueError:
            return

        # Only process if the slider values have changed
        if self.last_values == slider_values:
            return  # Data hasn't changed; ignore it.
        self.last_values = slider_values

        if reversed:
            # Map slider values to volume: 0 -> 1.0 (fader up), 1023 -> 0.0 (fader down)
            volumes = [(1023 - value) / 1023 for value in slider_values]
        else:
            volumes = [value / 1023 for value in slider_values]

        # Slider 0 controls master volume
        self.set_master_volume(volumes[0])

        # Sliders 1 to 4 control specific applications.
        for idx in range(1, len(slider_mapping) + 1):
            mapping = slider_mapping.get(idx)
            if mapping:
                if isinstance(mapping, list):
                    for app in mapping:
                        self.set_volume_for_app(app, volumes[idx])
                else:
                    self.set_volume_for_app(mapping, volumes[idx])

    def set_master_volume(self, volume):
        default_sink_name = self.pulse.server_info().default_sink_name
        default_sink = next((sink for sink in self.pulse.sink_list() 
                             if sink.name == default_sink_name), None)
        if default_sink is not None:
            new_vol = PulseVolumeInfo([volume] * len(default_sink.volume.values))
            self.pulse.volume_set(default_sink, new_vol)

    def set_volume_for_app(self, app_name, volume):
        sink_inputs = self.pulse.sink_input_list()
        found = False
        for sink_input in sink_inputs:
            if sink_input.proplist.get('application.name') == app_name:
                new_vol = PulseVolumeInfo([volume] * len(sink_input.volume.values))
                self.pulse.volume_set(sink_input, new_vol)
                found = True

    def connection_lost(self, exc):
        print("Serial connection lost.")
        if not self.connection_lost_future.done():
            self.connection_lost_future.set_result(True)

async def main():
    loop = asyncio.get_running_loop()
    serial_port = '/dev/ttyACM0'
    baud_rate = 115200

    while True:
        try:
            # Attempt to create a serial connection.
            print(f"Trying to connect to {serial_port} at {baud_rate} baud...")
            transport, protocol = await serial_asyncio.create_serial_connection(
                loop, lambda: SerialReaderProtocol(pulse), serial_port, baudrate=baud_rate
            )
            # Wait until the protocol signals that the connection was lost.
            await protocol.connection_lost_future
            print("Connection closed. Reconnecting...")
        except Exception as e:
            print("Error during serial connection:", e)
        # Wait before attempting to reconnect.
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
