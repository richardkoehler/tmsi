"""
The original file has been modified by Richard Köhler.

(c) 2022,2023 Twente Medical Systems International B.V., Oldenzaal The Netherlands

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######  #     #   #####   #
   #     ##   ##  #
   #     # # # #  #        #
   #     #  #  #   #####   #
   #     #     #        #  #
   #     #     #        #  #
   #     #     #  #####    #

/**
 * @file ${example_stream_lsl.py}
 * @brief This example shows the functionality to stream to LSL.
 *
 */


"""

import sys
from os.path import dirname, join, realpath

from tmsi.TMSiFileFormats.file_writer import FileFormat, FileWriter
from tmsi.TMSiSDK.tmsi_errors.error import (
    TMSiError,
)
from tmsi.TMSiSDK.tmsi_sdk import (
    DeviceInterfaceType,
    DeviceState,
    DeviceType,
    TMSiSDK,
)


def main() -> None:
    Example_dir = dirname(realpath(__file__))  # directory of this file
    modules_dir = join(Example_dir, "..")  # directory with all modules
    sys.path.append(modules_dir)
    try:
        # Execute a device discovery. This returns a list of device-objects for every discovered device.
        TMSiSDK().discover(
            dev_type=DeviceType.saga,
            dr_interface=DeviceInterfaceType.docked,
            ds_interface=DeviceInterfaceType.usb,
        )
        discoveryList = TMSiSDK().get_device_list(DeviceType.saga)

        if len(discoveryList) > 0:
            # Get the handle to the first discovered device.
            dev = discoveryList[0]

            # Open a connection to the SAGA-system
            dev.open()

            # Initialise the lsl-stream
            stream = FileWriter(FileFormat.lsl, "SAGA")

            # Pass the device information to the LSL stream.
            stream.open(dev)

            # Close the file writer after GUI termination
            stream.close()

            # Close the connection to the SAGA device
            dev.close()

    except TMSiError as e:
        print(e)

    finally:
        # Close the connection to the device when the device is opened
        if "dev" in locals() and dev.get_device_state() == DeviceState.connected:
            dev.close()


if __name__ == "__main__":
    main()
