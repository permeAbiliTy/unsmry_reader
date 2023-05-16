#!/usr/bin/env python
# coding: utf-8

# Used to convert bytes to double
import struct

# Used to convert a set of integers to date
import datetime

# Methods return a pandas dataframe
import pandas as pd

# Used for stripping extension from filename
import os.path

class SummaryData:
    """An object which represents one Eclipse summary file 

    Parameters:
    root_name (string): The root name of the summary file to be processed. 
    """
    
    def __init__(self, root_name):
        """Initialises the SMSPEC and UNSMRY file names on creation of a SummaryData object

        Parameters:
        root_name (string): The root name of the summary file to be processed.

        """
        
        #strip extension from filename
        root_name = os.path.splitext(root_name)[0]
        
        self.SMSPECfile = root_name + '.SMSPEC' 
        self.UNSMRYfile = root_name + '.UNSMRY'

        
    def read_smspec(self, print_results=False):
        """Read the .SMSPEC file which includes information about the model and the expected structure of the .UNSMRY file.
        Results can be printed, allowing the model information and vector labels, well/group names, units, etc to be viewed.

        Parameters:
        print_results (bool): Flag for whether to print the data read from the .SMSPEC file. This can result in a large amount of information printed. 

        Returns:
        String: Contents of summary spec file if print_results is set to True

       """
        with open(self.SMSPECfile, "rb") as f:
            while True:
                section_name, num_records, record_type = self.read_block_header(f)
                if print_results:
                    print('Section: {}, expected records: {}:, record type: {}'.format(section_name, num_records, record_type))
                    
                if section_name == 'INTEHEAD':
                    self.intehead_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'RESTART':
                    self.restart_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'DIMENS':
                    self.dimens_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'STARTDAT':
                    self.startdat_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'RUNTIMEI':
                    self.runtimei_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'RUNTIMED':
                    self.runtimed_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'KEYWORDS':
                    self.keywords_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'WGNAMES':
                    # Ensure that blank strings ':+:+:+:+' are removed
                    self.wgnames_section = [w.replace(':+:+:+:+', '') for w in self.read_record(f, 
                                                                                                num_records,
                                                                                                record_type, 
                                                                                                print_results)]
                elif section_name == 'NUMS':
                    self.nums_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'MEASRMNT':
                    self.measrmnt_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == 'UNITS':
                    self.units_section = self.read_record(f, num_records, record_type, print_results)
                elif section_name == '':
                    if print_results:
                        print('End of file reached')
                    break
                else:
                    raise Exception('Unexpected section name ({})'.format(section_name))
        return

    
    def process_smspec(self):
        """Create start_date which is the simulation start date and nlist which contains the information from the dimensions section of the .SMSPEC file

        Parameters:
        None

        """
        self.nlist = self.dimens_section[0]
        self.start_date = datetime.datetime(day=self.startdat_section[0], 
                                            month=self.startdat_section[1],
                                            year=self.startdat_section[2],
                                            hour=self.startdat_section[3],
                                            minute=self.startdat_section[4],
                                            microsecond=self.startdat_section[5]
                                            )

        
    def read_block_header(self,f):
        """Reads a block header from the .UNSMRY file

        Parameters:
        f (file): The .SMSPEC or .UNSMRY file

        Returns:
        Tuple: (section_name, num_records, record_type)
        section_name (string): The name of the section
        num_records (int):     The number of records in the section
        record_type (string):  The data type of the data in the section

        """
        block_length = self.read_integers(f)[0]
        section_name = self.read_strings(f)[0]
        num_records = self.read_integers(f)[0]
        record_type = self.read_strings_short(f)[0]
        end_block_length = self.read_integers(f)[0]
        if block_length != end_block_length:
            raise Exception('Start block length ({}) not equal to end block length ({}).'.format(block_length, 
                                                                                                 end_block_length))
        else:
            return section_name, num_records, record_type

        
    def read_record(self, f, num_records, record_type, print_results):
        """Read in one section from .SMSPEC or .UNSMRY file

        Parameters:
        f (file): The .SMSPEC or .UNSMRY file
        num_records (int):    The number of records in the section
        record_type (string): The data type of the data in the section 
        print_results (bool): Flag for whether to print the data read from the .SMSPEC file

        Returns:
        String: Contents of section if print_results is set to True

        """
        section_results = list()
        i = 1
        while i <= num_records:
            if print_results:
                print('Reading record {} of {}'.format(i, num_records))
            block = list()
            block_length = self.read_integers(f)[0]
            if record_type == 'INTE':
                block = self.read_integers(f, block_length)
            elif record_type == 'REAL':
                block = self.read_reals(f, block_length)
            elif record_type == 'DOUB':
                block = self.read_doubles(f, block_length)
            elif record_type == 'CHAR':
                block = self.read_strings(f, block_length)
            elif record_type == 'LOGI':
                block = self.read_logis(f, block_length)
            else:
                raise Exception('Unrecognised record type: {}.'.format(record_type))
            end_block_length = self.read_integers(f)[0]
            if block_length != end_block_length:
                raise Exception('Start block length ({}) not equal to end block length ({}).'.format(block_length, 
                                                                                                     end_block_length))
            #print (block)
            i += len(block)
            section_results += block
        if print_results:
            print (section_results)
        return section_results

    
    def read_unsmry(self, print_results=False):
        """Read the whole .UNSMRY file which contains the vectors described in the .SMSPEC file.
        Results can be printed, however, this is not a useful way of viewing the data as there is usually a large amount.

        Parameters:
        print_results (bool): Flag for whether to print the data read from the .UNSMRY file. This can result in a large amount of information printed. 

        Returns:
        String: Contents of summary spec file if print_results is set to True

        """
        with open(self.UNSMRYfile, "rb") as f:
            self.seqhdr = list()
            self.ministep = list()
            self.params = list()
            while True:
                section_name, num_records, record_type = self.read_block_header(f)
                if print_results:
                    print('Section: {}, expected records: {}:, record type: {}'.format(section_name, 
                                                                                       num_records, 
                                                                                       record_type))
                if section_name == 'SEQHDR':
                    self.seqhdr.append(self.read_record(f, num_records, record_type, print_results))
                elif section_name == 'MINISTEP':
                    self.ministep.append(self.read_record(f, num_records, record_type, print_results))
                elif section_name == 'PARAMS':
                    self.params.append(self.read_record(f, num_records, record_type, print_results))
                elif section_name == '':
                    if print_results:
                        print('End of file reached')
                    break
                else:
                    raise Exception('Unexpected section name ({})'.format(section_name))
        self.dfparams = pd.DataFrame(self.params)
        return

    
    def vector(self, keyword, identifier):
        """Return a single vector from the datafile

        Parameters:
        keyword (string):    The vector to return
        identifier (string): The identifier (well/group, etc) for the vector

        Returns:
        dataframe : Eclipse summary vector

        """
        i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))
        return self.dfparams[i]

    
    # Set up functions to read the different types and return a list. 
    # Count is specified as a total number of bytes which should be divisible by the data length.
    # If no count is specified, it defaults to the length of one data item.

    def read_strings(self, f, count=8):
        """Read 8-character strings from the .SMSPEC or .UNSMRY file

        Parameters:
        f (file):    The .SMSPEC or .UNSMRY file
        count (int): The number of strings to be read

        Returns:
        list(string) : The strings read from the file

        """
        strings = list()
        length = 8
        for i in range(0,count//length):
            strings.append(f.read(length).decode(encoding='utf-8', errors='strict').strip())
    #        print('iteration {}'.format(i))
    #        a = f.read(length)
    #        print(a)
    #        b = a.decode(encoding='utf-8', errors='strict')
    #        print(b)
    #        strings.append(b)
        return strings

    def read_strings_short(self, f, count=4):
        """Read 4-character strings from the .SMSPEC or .UNSMRY file (mainly used for the data type descriptors)

        Parameters:
        f (file):    The .SMSPEC or .UNSMRY file
        count (int): The number of strings to be read

        Returns:
        list(string) : The strings read from the file

        """
        strings = list()
        length = 4
        for i in range(0,count//length):
            strings.append(f.read(length).decode(encoding='utf-8', errors='strict'))
        return strings

    def read_integers(self, f, count=4):
        """Read INTEs from the .SMSPEC or .UNSMRY file

        Parameters:
        f (file):    The .SMSPEC or .UNSMRY file
        count (int): The number of INTEs to be read

        Returns:
        list(integer) : The INTEs read from the file

        """
        integers = list()
        length = 4
        for i in range(0,count//length):
            integers.append(int.from_bytes(f.read(length), byteorder='big'))
        return integers

    def read_doubles(self, f, count=8):
        """Read DOUBs from the .SMSPEC or .UNSMRY file

        Parameters:
        f (file):    The .SMSPEC or .UNSMRY file
        count (int): The number of DOUBs to be read

        Returns:
        list(float) : The DOUBs read from the file

        """
        doubles = list()
        length = 8
        for i in range(0,count//length):
            doubles.append(struct.unpack('<d',f.read(length)))
        return doubles

    def read_reals(self, f, count=4):
        """Read REALs from the .SMSPEC or .UNSMRY file

        Parameters:
        f (file):    The .SMSPEC or .UNSMRY file
        count (int): The number of REALs to be read

        Returns:
        list(float) : The REALs read from the file

        """
        reals = list()
        length = 4
        for i in range(0,count//length):
            reals.append(struct.unpack('>f',f.read(length))[0])
        return reals

    def read_logis(self, f, count=4):
        """Read LOGIs from the .SMSPEC or .UNSMRY file

        Parameters:
        f (file):    The .SMSPEC or .UNSMRY file
        count (int): The number of LOGIs to be read

        Returns:
        list(integer) : The LOGIs read from the file

        """
        logis = list()
        length = 4
        for i in range(0,count//length):
            logis.append((int.from_bytes(f.read(length), byteorder='big'))>0)
        return logis

    
if __name__ == '__main__':
    print('This script should be imported as a module')
else:
    print('Importing summary file processing script')
