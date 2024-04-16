"""
The original file has been modified by Richard Köhler.

(c) 2022 Twente Medical Systems International B.V., Oldenzaal The Netherlands

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
 * @file ${__init__.py}
 * @brief Initialisation of the TMSiFileFormats directory classes.
 *
 */


"""

from .file_writer import FileFormat, FileWriter
from .file_formats.lsl_stream_writer import LSLWriter
from .file_formats.mne_lsl_writer import MNELSLWriter
from .file_formats.poly5_file_writer import Poly5Writer
from .file_formats.poly5_to_edf_converter import Poly5_to_EDF_Converter
from .file_formats.xdf_file_writer import XdfWriter
from .file_readers.poly5reader import Poly5Reader
from .file_readers.xdf_reader import Xdf_Reader
from .file_readers.edf_reader import Edf_Reader
