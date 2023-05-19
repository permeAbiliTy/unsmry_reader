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
	
	Methods:
		read_smspec(print_results=False): 	Read the .SMSPEC file which includes information about the model and the expected structure of the .UNSMRY file.
												Optionally prints results, allowing the model information and vector labels, well/group names, units, etc to be viewed.
												
		process_smspec(): 					Create start_date which is the simulation start date and nlist which contains the information from the dimensions section of the .SMSPEC file
		
		read_unsmry(print_results=False): 	Read the whole .UNSMRY file which contains the vectors described in the .SMSPEC file.
												Optionally prints results, however, this is not a useful way of viewing the data as there is usually a large amount.
													
		vector(keyword, identifier):		Return a single vector from the summary data, either from data read in using read_unsmry() or else directly from .unsmry file
													
    """
    
    def __init__(self, root_name):
        """Initialises the SMSPEC and UNSMRY file names on creation of a SummaryData object

        Parameters:
            root_name (string): The root name of the summary file to be processed.
        
        Attributes:
            SMSPECfile (string): The name of the .SMSPEC file
            UNSMRYfile (string): The name of the .UNSMRY file
            __on_demand (bool):  Flag determining whether to read vectors individually from .unsmry file or read in whole summary file
                                        This flag is set to False until read_unsmry() is run, which reads whole summary file to memory
        """
        
        #strip extension from filename
        root_name = os.path.splitext(root_name)[0]
        
        self.SMSPECfile = root_name + '.SMSPEC' 
        self.UNSMRYfile = root_name + '.UNSMRY'
        
        #Flag for whether to load results on demand, start with this set to True and set to false when whole summary is read in read_unsmry()
        self.__on_demand = True

        
    def read_smspec(self, print_results=False):
        """Read the .SMSPEC file which includes information about the model and the expected structure of the .UNSMRY file.
        Results can be printed, allowing the model information and vector labels, well/group names, units, etc to be viewed.

        Parameters:
            print_results (bool): Flag for whether to print the data read from the .SMSPEC file. This can result in a large amount of information printed. 
        
        Attributes:
            intehead_section (list): The contents of the intehead section from the .SMSPEC file
                                        Item 1 - units type: 1 – METRIC, 2 – FIELD, 3 –LAB, 4 - PVT-M
                                        Item 2 - simulation program identifier:
            restart_section (list): The contents of the restart section from the .SMSPEC file
                                        Root name of restart file from which this run originated (if any), up to 72 characters divided into 8-character words
            dimens_section (list): The contents of the dimens section from the .SMSPEC file
                                        Item 1 - NLIST = number of data vector parameters stored at each timestep
                                        Item 2 - NDIVIX = number of cells in X-direction
                                        Item 3 - NDIVIY = number of cells in Y-direction
                                        Item 4 - NDIVIZ = number of cells in Z-direction
                                        Item 5 - Dummy
                                        Item 6 - ISTAR = report step number of restart file used to start this run (if any)
            startdat_section (list): The contents of the startdat section from the .SMSPEC file
                                        The date of the run start
                                            (a) Day (1-31)
                                            (b) Month (1-12)
                                            (c) Year (as four digits, for example 1952)
                                            (d) Hour (0-23)
                                            (e) Minute (0-59)
                                            (f) Second (expressed in microseconds, 0-59,999,999)
            runtimei_section (list): The contents of the runtimei section from the .SMSPEC file
                                        Integer data used for run-time monitoring
                                            Item 1: 2 if the simulation is finished, 1 otherwise
                                            Item 2: initial report number
                                            Item 3: current report number
                                            Items 4 to 9: initial clock date and time as YYYY, MM, DD, HH, MM, SS
                                            Items 10 to 15: most recent clock date and time as YYYY, MM, DD, HH, MM, SS
                                            Item 35: value assigned to “BASIC” mnemonic in the RPTRST keyword
            runtimed_section (list): The contents of the runtimed section from the .SMSPEC file
                                        Double precision data used for run-time monitoring
            keywords_section (list): The contents of the keywords section from the .SMSPEC file
                                        The mnemonic keyword associated with each data vector
            wgnames_section (list): The contents of the wgnames section from the .SMSPEC file
                                        The well or group name associated with each data vector
            nums_section (list): The contents of the nums section from the .SMSPEC file
                                        The integer cell or region number associated with each data vector
            measrmnt_section (list): The contents of the intehead measrmnt from the .SMSPEC file
                                        Measurements associated with each vector. 
            units_section (list): The contents of the intehead section from the .SMSPEC file
                                        Units associated with each vector, used when assigning axes to a line graph

        Raises:
            Exception: if an unexpected section name encountered while reading .SMSPEC file
            
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
        self.process_smspec()
        return

    
    def process_smspec(self):
        """Create start_date which is the simulation start date and nlist which contains the information from the dimensions section of the .SMSPEC file

        Parameters:
            None
        
        Attributes:
            nlist (int):                 Number of data vector parameters stored at each timestep
            start_date (datetime):       The date of the run start
            well_names (list, strings):  A list of the unique well names available in summary file
            group_names (list, strings): A list of the unique group names available in summary file
            vector_names (list, strings):A list of the unique vector names available in summary file

        """
        self.nlist = self.dimens_section[0]
        self.start_date = datetime.datetime(day=self.startdat_section[0], 
                                            month=self.startdat_section[1],
                                            year=self.startdat_section[2],
                                            hour=self.startdat_section[3],
                                            minute=self.startdat_section[4],
                                            #Eclipse does not give seconds, datetime does not accept microseconds > 999999, so split to seconds and microseconds
                                            second=self.startdat_section[5] // 1000000,
                                            microsecond=self.startdat_section[5] % 1000000
                                            )
        self.well_names = list()
        self.group_names = list()
        self.vector_names = list()
        for keyword, wgname in list(zip(self.keywords_section, self.wgnames_section)):
 #           print('keyword: {}, wgname: {}'.format(keyword, wgname))
            if keyword[0] == 'W' and wgname not in self.well_names:
                self.well_names.append(wgname)
            elif keyword[0] == 'G' and wgname not in self.group_names:
                self.group_names.append(wgname)
            if keyword not in self.vector_names:
                self.vector_names.append(keyword)
        # Remove any empty strings
        self.well_names = [x for x in self.well_names if x != '']
        self.group_names = [x for x in self.group_names if x != '']
        self.vector_names = [x for x in self.vector_names if x != '']
        return            

        
    def read_block_header(self,f):
        """Reads a block header from the .UNSMRY file

        Parameters:
            f (file): The .SMSPEC or .UNSMRY file

        Returns:
            Tuple: (section_name, num_records, record_type)
            section_name (string): The name of the section
            num_records (int):     The number of records in the section
            record_type (string):  The data type of the data in the section
        
        Raises:
            Exception: If the record of the block length at the start and end of a block do not match

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
        Results can be printed, allowing the contents of the current record to be viewed

        Parameters:
            f (file):             The .SMSPEC or .UNSMRY file
            num_records (int):    The number of records in the section
            record_type (string): The data type of the data in the section 
            print_results (bool): Flag for whether to print the data read from the .SMSPEC file

        Returns:
            List: Contents of section
            
        Raises:
            Exception: If the record of the block length at the start and end of a block do not match

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
    
    def read_record_on_demand(self, f, read_index, num_records, record_type):
        """Read in one item from a section in .SMSPEC or .UNSMRY file, seeking past undesired data

        Parameters:
            f (file):             The .SMSPEC or .UNSMRY file
            read_index (int):     The index of the vector to be read
            num_records (int):    The number of records in the section
            record_type (string): The data type of the data in the section 
            print_results (bool): Flag for whether to print the data read from the .SMSPEC file

        Returns:
            Result: Contents of requested item
            
        Raises:
            Exception: If the record of the block length at the start and end of a block do not match

        """
        result = list()
        
        if record_type in ['DOUB', 'CHAR']:
            type_length = 8
        else:
            type_length = 4
        target = read_index + 1
            
        i = 1
        while i <= num_records:
            block_length = self.read_integers(f)[0]
            if target > (i + block_length//type_length) or target < i:
                #print('Current record: {}, block length: {}, target: {} - Skipping block'.format(i, block_length, target))
                f.seek(block_length, 1)
            else:
                skip_num = (target - i) * type_length
                #print('Current record: {}, block length: {}, target: {} - Skipping {}, reading 1, skipping {}'.format(i, block_length//type_length, target, skip_num, block_length-skip_num-2))
                if record_type == 'INTE':
                    f.seek(skip_num, 1)
                    result = self.read_integers(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'REAL':
                    f.seek(skip_num, 1)
                    result = self.read_reals(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'DOUB':
                    f.seek(skip_num, 1)
                    result = self.read_doubles(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'CHAR':
                    f.seek(skip_num, 1)
                    result = self.read_strings(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'LOGI':
                    f.seek(skip_num, 1)
                    result = self.read_logis(f)
                    f.seek((block_length-skip_num-type_length), 1)
                else:
                    raise Exception('Unrecognised record type: {}.'.format(record_type))    
            end_block_length = self.read_integers(f)[0]
            if block_length != end_block_length:
                raise Exception('Start block length ({}) not equal to end block length ({}).'.format(block_length, 
                                                                                                     end_block_length))
            #print (block)
            i += block_length//type_length
            
        return result

    
    def read_unsmry(self, print_results=False):
        """Read the whole .UNSMRY file which contains the vectors described in the .SMSPEC file.
        Results can be printed, however, this is not a useful way of viewing the data as there is usually a large amount.

        Parameters:
            print_results (bool): Flag for whether to print the data read from the .UNSMRY file. This can result in a large amount of information printed.
            
        Attributes:
            seqhdr (list): The contents of the seqhdr sections from the .UNSMRY file
                                ISNUM = an encoded integer corresponding to the time the file was created.
            ministep (list): The contents of the ministep sections from the .UNSMRY file
                                Ministep numbers (starting at zero and incremented by 1 at each subsequent step)
            params (list): The contents of the params sections from the .UNSMRY file
                                Vector parameter values at each ministep (corresponding to the vectors defined in the specification file)
            dfparams (dataframe): A dataframe containing the summary data
            
        Raises:
            Exception: if an unexpected section name encountered while reading .SMSPEC file
        
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
        
        #Summary file has been read in so set the on demand flag to False
        self.__on_demand = False
        return

    
    def vector(self, keyword, identifier):
        """Return a single vector from the summary data, either from data read in using read_unsmry() or else directly from .unsmry file

        Parameters:
            keyword (string):    The vector to return
            identifier (string): The identifier (well/group, etc) for the vector

        Returns:
            dataframe : Eclipse summary vector

        """
        i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))
        #print(i)
        if not self.__on_demand:
            #Return vector from whole summary file that has already been read
            return self.dfparams[i]
        else:
            #seek through summary file to pull out individual vector
            with open(self.UNSMRYfile, "rb") as f:
                self.param = list()
                while True:
                    section_name, num_records, record_type = self.read_block_header(f)
                    
                    if section_name == 'SEQHDR':
                        self.read_record_on_demand(f, 9999, num_records, record_type)
                    elif section_name == 'MINISTEP':
                        self.read_record_on_demand(f, 9999, num_records, record_type)
                    elif section_name == 'PARAMS':
                        self.param.append(self.read_record_on_demand(f, i, num_records, record_type))
                    elif section_name == '':
                        break
                    else:
                        raise Exception('Unexpected section name ({})'.format(section_name))
            self.param = pd.DataFrame(self.param)
            return self.param[0]
        return

    
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