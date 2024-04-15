"""
The original file has been modified by Richard Köhler.

(c) 2023 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @file impedance_measurement.py
 * @brief
 * Class to handle the communication with the device for  impedance acquisition.
 */


"""

import time
from copy import deepcopy
from ctypes import *

from .....sample_data_server.sample_data import SampleData
from .....sample_data_server.sample_data_server import (
    SampleDataServer,
    TMSiLoggerActivity,
)
from .....tmsi_utilities.decorators import LogPerformances
from .....tmsi_utilities.tmsi_logger import TMSiLogger as logger
from ....tmsi_measurement import TMSiMeasurement
from ..apex_API_enums import ImpedanceControl, TMSiDeviceRetVal
from ..apex_API_structures import TMSiDevImpedanceRequest, TMSiImpedanceSample


class ImpedanceMeasurement(TMSiMeasurement):
    """Class to handle the Impedance measurements."""

    def __init__(self, dev, name="Impedance Measurement"):
        """Initialize the EEG measurement.

        :param dev: Device to measure from.
        :type dev: TMSiDevice
        :param name: name of the measurement, defaults to "Impedance Measurement"
        :type name: str, optional
        """
        super().__init__(dev=dev, name=name)
        self._sample_data_buffer = (TMSiImpedanceSample * self._sample_data_buffer_size)(
            TMSiImpedanceSample()
        )
        self._num_samples_per_set = dev.get_num_impedance_channels()

    @LogPerformances
    def _sampling_function(self):
        TMSiLoggerActivity().log("Sampling Thread->>APEX-SDK: GET impedance samples request")
        ret = self._dev.get_device_impedance_data(
            pointer(self._sample_data_buffer),
            self._sample_data_buffer_size,
            pointer(self._retrieved_sample_sets),
        )
        TMSiLoggerActivity().log("APEX-SDK->>Sampling Thread: GET impedance samples response")
        if ret == TMSiDeviceRetVal.TMSiStatusOK:
            TMSiLoggerActivity().log("Sampling Thread->>Sampling Thread: positive response")
            if self._retrieved_sample_sets.value > 0:
                self._conversion_queue.put(
                    (
                        deepcopy(self._sample_data_buffer),
                        self._retrieved_sample_sets.value,
                    )
                )
                TMSiLoggerActivity().log(
                    f"Sampling Thread->>Conversion Queue: PUT samples | package size:{self._retrieved_sample_sets.value} - new size:{self._conversion_queue.qsize()}"
                )
                self._empty_read_counter = 0
            else:
                TMSiLoggerActivity().log("Sampling Thread->>Sampling Thread: empty package")
                if self._empty_read_counter == 0:
                    self._tic_timeout = time.perf_counter()
                self._empty_read_counter += 1
        else:
            TMSiLoggerActivity().log(f"APEX-SDK->>Sampling Thread: negative response: {ret}")

    @LogPerformances
    def _conversion_function(self):
        while not self._conversion_queue.empty():
            sample_data_buffer, retrieved_sample_sets = self._conversion_queue.get()
            TMSiLoggerActivity().log(
                f"Conversion Queue->>Conversion Thread: GET samples | package size:{retrieved_sample_sets} - new size:{self._conversion_queue.qsize()}"
            )
            if retrieved_sample_sets > 0:
                sample_mat = [
                    sample_data_buffer[
                        ii : retrieved_sample_sets * self._num_samples_per_set : self._num_samples_per_set
                    ]
                    for ii in range(self._num_samples_per_set)
                ]
                samples_exploded = [
                    [i.ImpedanceRe if ii % 2 == 0 else i.ImpedanceIm for i in sample_mat[ii // 2]]
                    for ii in range(self._num_samples_per_set * 2)
                ]
                samples_exploded_inline = [
                    samples_exploded[i][j]
                    for j in range(len(samples_exploded[0]))
                    for i in range(len(samples_exploded))
                ]
                sd = SampleData(
                    retrieved_sample_sets,
                    self._num_samples_per_set * 2,
                    samples_exploded_inline,
                )
                TMSiLoggerActivity().log(
                    "Conversion Thread->>Conversion Thread: convert samples to sample data"
                )
                TMSiLoggerActivity().log("Conversion Thread->>SDS: PUT sample data")
                SampleDataServer().put_sample_data(self._dev.get_id(), sd)
                logger().debug(
                    f"Data delivered to sample data server: {self._num_samples_per_set} channels, {retrieved_sample_sets} samples"
                )

    @LogPerformances
    def start(self):
        """Start the measurement."""
        self._dev.reset_device_data_buffer()
        measurement_request = TMSiDevImpedanceRequest()
        measurement_request.StartStop = ImpedanceControl.StartImpedance.value
        TMSiLoggerActivity().log(f"{self.get_name()}->>APEX-SDK: set device impedance request ON")
        self._dev.set_device_impedance_request(measurement_request)
        TMSiLoggerActivity().log(f"{self.get_name()}->>Sampling Thread: start")
        self._sampling_thread.start()
        TMSiLoggerActivity().log(f"{self.get_name()}->>Conversion Thread: start")
        self._conversion_thread.start()

    @LogPerformances
    def stop(self):
        """Stop the measurement."""
        measurement_request = TMSiDevImpedanceRequest()
        measurement_request.StartStop = ImpedanceControl.StopImpedance.value
        TMSiLoggerActivity().log(f"{self.get_name()}->>APEX-SDK: set device impedance request OFF")
        self._dev.set_device_impedance_request(measurement_request)
        TMSiLoggerActivity().log(f"{self.get_name()}->>Sampling Thread: stop")
        self._sampling_thread.stop()
        self._sampling_thread.join()
        TMSiLoggerActivity().log(f"{self.get_name()}->>Conversion Thread: stop")
        self._conversion_thread.stop()
        self._conversion_thread.join()
