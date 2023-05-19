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
        root_name (string):     The root name of the summary file to be processed. 
        on_demand (boolean):    Specify whether to read whole summary file at start, or to read from summary file for each vector
        print_smspec:           Results can be printed, allowing the model information and vector labels, well/group names, units, etc to be viewed
        print_unsmry:           Results can be printed, however, this is not a useful way of viewing the data as there is usually a large amount

    Attributes:
        nlist (int):                    Number of data vector parameters stored at each timestep
        start_date (datetime):          The date of the run start
        well_names (list, strings):     A list of the unique well names available in summary file
        group_names (list, strings):    A list of the unique group names available in summary file
        vector_names (list, strings):   A list of the unique vector names available in summary file
    
    Methods:
        vector(keyword, identifier):    Return a single vector from the summary data, either from data read in using __read_unsmry() or else directly from .unsmry file
                                                    
    """
    
    def __init__(self, root_name, on_demand=True, print_smspec=False, print_unsmry=False):
        """Initialises the SummaryData object and processes the SMSPEC file

        Parameters:
            root_name (string): 	The root name of the summary file to be processed.
			on_demand (bool):		Flag for whether to load in whole summary file, or fetch vectors on-demand (default=True)
			print_smspec (bool):	Flag for whether to print the data read from the .SMSPEC file. This can result in a large amount of information printed. (default=False)
			print_unsmry (bool):	Flag for whether to print the data read from the .UNSMRY file. This can result in a large amount of information printed. (default=False)
        
        Attributes:
            SMSPECfile (string): The name of the .SMSPEC file
            UNSMRYfile (string): The name of the .UNSMRY file
            __on_demand (bool):  Flag determining whether to read vectors individually from .unsmry file or read in whole summary file
        """
        
        #strip extension from filename
        root_name = os.path.splitext(root_name)[0]
        
        self.SMSPECfile = root_name + '.SMSPEC' 
        self.UNSMRYfile = root_name + '.UNSMRY'
        
        self.__read_smspec(print_results=print_smspec)
        self.__process_smspec()
         
        #Flag for whether to load results on demand, by default set to True
        self.__on_demand = on_demand
        
        if self.__on_demand == False:
            self.____read_unsmry(print_results=print_unsmry)

        
    def __read_smspec(self, print_results=False):
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
                section_name, num_records, record_type = self.__read_block_header(f)
                if print_results:
                    print('Section: {}, expected records: {}:, record type: {}'.format(section_name, num_records, record_type))
                    
                if section_name == 'INTEHEAD':
                    self.intehead_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'RESTART':
                    self.restart_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'DIMENS':
                    self.dimens_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'STARTDAT':
                    self.startdat_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'RUNTIMEI':
                    self.runtimei_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'RUNTIMED':
                    self.runtimed_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'KEYWORDS':
                    self.keywords_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'WGNAMES':
                    # Ensure that blank strings ':+:+:+:+' are removed
                    self.wgnames_section = [w.replace(':+:+:+:+', '') for w in self.__read_record(f, 
                                                                                                num_records,
                                                                                                record_type, 
                                                                                                print_results)]
                elif section_name == 'NUMS':
                    self.nums_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'MEASRMNT':
                    self.measrmnt_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == 'UNITS':
                    self.units_section = self.__read_record(f, num_records, record_type, print_results)
                elif section_name == '':
                    if print_results:
                        print('End of file reached')
                    break
                else:
                    raise Exception('Unexpected section name ({})'.format(section_name))
        return

    
    def __process_smspec(self):
        """Create start_date which is the simulation start date and nlist which contains the information from the dimensions section of the .SMSPEC file

        Parameters:
            None
        
        Attributes:
            nlist (int):                 Number of data vector parameters stored at each timestep
            nx (int):                    Grid NX    
            ny (int):                    Grix NY
            nz (int):                    Grid NZ
            start_date (datetime):       The date of the run start
            well_names (list, strings):  A list of the unique well names available in summary file
            group_names (list, strings): A list of the unique group names available in summary file
            vector_names (list, strings):A list of the unique vector names available in summary file

        """
        self.nlist = self.dimens_section[0]
        self.nx = self.dimens_section[1]
        self.ny = self.dimens_section[2]
        self.nz = self.dimens_section[3]
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

        
    def __read_block_header(self,f):
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
        block_length = self.__read_integers(f)[0]
        section_name = self.__read_strings(f)[0]
        num_records = self.__read_integers(f)[0]
        record_type = self.__read_strings_short(f)[0]
        end_block_length = self.__read_integers(f)[0]
        if block_length != end_block_length:
            raise Exception('Start block length ({}) not equal to end block length ({}).'.format(block_length, 
                                                                                                 end_block_length))
        else:
            return section_name, num_records, record_type

        
    def __read_record(self, f, num_records, record_type, print_results):
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
            block_length = self.__read_integers(f)[0]
            if record_type == 'INTE':
                block = self.__read_integers(f, block_length)
            elif record_type == 'REAL':
                block = self.__read_reals(f, block_length)
            elif record_type == 'DOUB':
                block = self.__read_doubles(f, block_length)
            elif record_type == 'CHAR':
                block = self.__read_strings(f, block_length)
            elif record_type == 'LOGI':
                block = self.__read_logis(f, block_length)
            else:
                raise Exception('Unrecognised record type: {}.'.format(record_type))
            end_block_length = self.__read_integers(f)[0]
            if block_length != end_block_length:
                raise Exception('Start block length ({}) not equal to end block length ({}).'.format(block_length, 
                                                                                                     end_block_length))
            i += len(block)
            section_results += block
        if print_results:
            print (section_results)
        return section_results
    
    def __read_record_on_demand(self, f, read_index, num_records, record_type):
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
            block_length = self.__read_integers(f)[0]
            if target > (i + block_length//type_length) or target < i:
                f.seek(block_length, 1)
            else:
                skip_num = (target - i) * type_length
                if record_type == 'INTE':
                    f.seek(skip_num, 1)
                    result = self.__read_integers(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'REAL':
                    f.seek(skip_num, 1)
                    result = self.__read_reals(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'DOUB':
                    f.seek(skip_num, 1)
                    result = self.__read_doubles(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'CHAR':
                    f.seek(skip_num, 1)
                    result = self.__read_strings(f)
                    f.seek((block_length-skip_num-type_length), 1)
                elif record_type == 'LOGI':
                    f.seek(skip_num, 1)
                    result = self.__read_logis(f)
                    f.seek((block_length-skip_num-type_length), 1)
                else:
                    raise Exception('Unrecognised record type: {}.'.format(record_type))    
            end_block_length = self.__read_integers(f)[0]
            if block_length != end_block_length:
                raise Exception('Start block length ({}) not equal to end block length ({}).'.format(block_length, 
                                                                                                     end_block_length))
            i += block_length//type_length
            
        return result

    
    def __read_unsmry(self, print_results=False):
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
                section_name, num_records, record_type = self.__read_block_header(f)
                if print_results:
                    print('Section: {}, expected records: {}:, record type: {}'.format(section_name, 
                                                                                       num_records, 
                                                                                       record_type))
                if section_name == 'SEQHDR':
                    self.seqhdr.append(self.__read_record(f, num_records, record_type, print_results))
                elif section_name == 'MINISTEP':
                    self.ministep.append(self.__read_record(f, num_records, record_type, print_results))
                elif section_name == 'PARAMS':
                    self.params.append(self.__read_record(f, num_records, record_type, print_results))
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

    
    def vector(self, keyword, identifier=''):
        """Return a single vector from the summary data, either from data read in using __read_unsmry() or else directly from .unsmry file

        Parameters:
            keyword (string):    The vector to return
            identifier (string): The identifier (well/group, etc) for the vector
                                    will accept inter-region vectors e.g. RWFT '1 2'
                                    will accept well connection quantities e.g. CWPR 'PRD_A 1'

        Returns:
            dataframe : Eclipse summary vector

        """
        
        #Look up keyword and identifier depending on vector type
        
        # Special keywords that do not follow usual pattern of first letters
        special_keywords = ['TIME', 'YEARS', 'DAY', 'MONTH', 'YEAR', 'ELAPSED', 'MAXDPR', 'MAXDSO', 'MAXDSG', 'MAXDSW', 'NEWTON', 'NLINEARS', 'STEPTYPE', 
                            'TCPU', 'TCPUTS', 'TCPUDAY', 'TELAPTS', 'TELAPDAY', 'TIMESTEP']
        sign_mult = 1
        
        if keyword in special_keywords:
            i = list(self.keywords_section).index((keyword)) 
            
        elif keyword[0] == 'A': # Aquifer
            i = list(zip(self.keywords_section, self.nums_section)).index((keyword, identifier))    
            
        elif keyword[0] == 'B': # Block data
            # "Cell index, calculated from the natural position as (IZ-1)*NX*NY+(IY-1)*NX+IX"
            #       - Eclipse File Formats Reference Manual
            block_ix, block_iy, block_iz = tuple(identifier.split())
            block_index = ((int(block_iz) - 1) * self.nx * self.ny) + ((int(block_iy) - 1) * self.nx) + int(block_ix)
            i = list(zip(self.keywords_section, self.nums_section)).index((keyword, block_index))   
            
        elif keyword[0] == 'C': # Completion or connection data
            well_name, connection_number = tuple(identifier.split())
            i = list(zip(self.keywords_section, self.wgnames_section, self.nums_section)).index((keyword, well_name, int(connection_number)))
            
        elif keyword[0] == 'E': # Edge data produced by the FrontSim GEOFLOFS option or the ELAPSED keyword
            i = list(self.keywords_section).index((keyword))
            
        elif keyword[0] == 'F': # Field data
            i = list(self.keywords_section).index((keyword))
            
        elif keyword[0] == 'G': # Group data
            i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))
            
        elif keyword[0:2] == 'LB': # Local grid block data
            raise Exception('Keywords starting LB for Local grid block data not currently supported ({})'.format(keyword))
            
        elif keyword[0:2] == 'LC': # Local grid completion or connection data
            raise Exception('Keywords starting LC for Local grid completion or connection data not currently supported ({})'.format(keyword))
            
        elif keyword[0:2] == 'LW': # Local grid well data
            raise Exception('Keywords starting LW for Local grid well data not currently supported ({})'.format(keyword))
            
        elif keyword[0] == 'N': # Network node or network general data
            i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))
            
        elif keyword[0] == 'P': # Network branch (or “pipe”) data
            i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))         

        elif keyword[0] == 'R' and keyword[2] == 'F': # Region to region flows
            # "Combined region number calculated as IR1 + 32768*(IR2+10) where flow is from IR1 to IR2"
            #       - Eclipse File Formats Reference Manual
            region_num1, region_num2 = tuple(identifier.split())
            combined_region_number_1 = int(region_num1) + (32768 * (int(region_num2) + 10))
            combined_region_number_2 = int(region_num2) + (32768 * (int(region_num1) + 10))
            try:
                i = list(zip(self.keywords_section, self.nums_section)).index((keyword, combined_region_number_1))
            except:
                try:
                    i = list(zip(self.keywords_section, self.nums_section)).index((keyword, combined_region_number_2))
                    sign_mult = -1
                except:
                    raise Exception('No result found for identifier {}, (NUMS {} or {})'.format(identifier, combined_region_number_1, combined_region_number_2))

        elif keyword[0:2] == 'RC' and keyword[3] == 'M': # Region with a component number
            # "Combined region and component number calculated as IR + 32768*(IC+10)"
            #       - Eclipse File Formats Reference Manual
            region_num, comp_num = tuple(identifier.split())
            combined_region_comp_number = int(region_num) + (32768 * (int(comp_num) + 10))
            i = list(zip(self.keywords_section, self.wgnames_section, self.nums_section)).index((keyword, well_name, combined_region_comp_number))  

        elif keyword[0] == 'R': # Region data
            # "Identifier: NUMS keyword. Optional WNAMES (or NAMES *) keyword for simulators that support named regions."
            #       - Eclipse File Formats Reference Manual
            #           Possible this may need modification to be compatible with WNAMES for Intersect if it supports named regions
            i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))
            
        elif keyword[0] == 'S': # Well segment data
            # "Well segment vectors require the well name and the segment number; other vectors beginning with S require no additional data"
            #       - Eclipse File Formats Reference Manual
            #           Not sure what 'other vectors' this refers to - need to be careful about this
            well_name, segment_number = tuple(identifier.split())
            i = list(zip(self.keywords_section, self.wgnames_section, self.nums_section)).index((keyword, well_name, segment_number))           

        elif keyword[0] == 'W': # Well or completion data
            i = list(zip(self.keywords_section, self.wgnames_section)).index((keyword, identifier))
        
        else:
            raise Exception('Unexpected keyword first letter ({}) in keyword {}'.format(keyword[0], keyword))

        if not self.__on_demand:
            #Return vector from whole summary file that has already been read
            return self.dfparams[i] * sign_mult
        else:
            #seek through summary file to pull out individual vector
            with open(self.UNSMRYfile, "rb") as f:
                self.param = list()
                while True:
                    section_name, num_records, record_type = self.__read_block_header(f)
                    
                    if section_name == 'SEQHDR':
                        self.__read_record_on_demand(f, 9999, num_records, record_type)
                    elif section_name == 'MINISTEP':
                        self.__read_record_on_demand(f, 9999, num_records, record_type)
                    elif section_name == 'PARAMS':
                        self.param.append(self.__read_record_on_demand(f, i, num_records, record_type))
                    elif section_name == '':
                        break
                    else:
                        raise Exception('Unexpected section name ({})'.format(section_name))
            self.param = pd.DataFrame(self.param)
            return self.param[0] * sign_mult
        return

    
    # Set up functions to read the different types and return a list. 
    # Count is specified as a total number of bytes which should be divisible by the data length.
    # If no count is specified, it defaults to the length of one data item.

    def __read_strings(self, f, count=8):
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
        return strings

    def __read_strings_short(self, f, count=4):
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

    def __read_integers(self, f, count=4):
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

    def __read_doubles(self, f, count=8):
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

    def __read_reals(self, f, count=4):
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

    def __read_logis(self, f, count=4):
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
