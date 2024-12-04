import os
import struct
import json

class Sogna:
    def __init__(self):
        self.input_dir = 'input_files'
        self.intermediate_dir = 'intermediate_files'
        self.intermediate_dir_win = 'intermediate_files/win'
        self.output_dir = 'output_files'
        self.target_dat_file = "SGS.DAT"
        self.signature = b'SGS.DAT 1.00'
        self.entry = []

        for directory in [self.input_dir, self.intermediate_dir, self.intermediate_dir_win, self.output_dir]:
            os.makedirs(directory, exist_ok=True)

    def extract_text(self, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
            
        data_len = len(content)
        content_length = data_len
        found_texts = []
        
        start_pos = 0
        
        while start_pos < data_len:
            if start_pos < data_len and content[start_pos] == 0x24 and content[start_pos + 2] == 0x81:
                text_start = start_pos + 2
                text_end = text_start
                
                while text_end < content_length and content[text_end] != 0:
                    text_end += 1
                    
                if text_end < content_length:
                    text_bytes = content[text_start:text_end]
                    text = text_bytes.decode('cp932')
                    if len(text) > 1:
                        found_texts.append({
                            'offset': start_pos,
                            'orig': text,
                            'trans': ''
                        })
                    start_pos = text_end + 1
                    continue

            if start_pos < data_len - 3 and content[start_pos] == 0x21 and content[start_pos + 1] in [i for i in range(0x80, 0x9F)]:
                text_start = start_pos + 1
                text_end = text_start
                
                while text_end < content_length and content[text_end] != 0:
                    text_end += 1
                    
                if text_end < content_length:
                    text_bytes = content[text_start:text_end]
                    text = text_bytes.decode('cp932')
                    if len(text) > 1:
                        found_texts.append({
                            'offset': start_pos,
                            'orig': text,
                            'trans': ''
                        })
                    start_pos = text_end + 1
                    continue
                    
            if start_pos < content_length - 2 and content[start_pos] == 0x21 and content[start_pos + 1] == 0x01 and 0 <= content[start_pos + 2] <= 10:
                text_start = start_pos + 3 
                text_end = text_start
                
                while text_end < content_length and content[text_end] != 0:
                    text_end += 1
                    
                if text_end < content_length:
                    text_bytes = content[text_start:text_end]
                    text = text_bytes.decode('cp932')
                    if len(text) > 1:
                        found_texts.append({
                            'offset': start_pos,
                            'orig': text,
                            'trans': ''
                        })
                    start_pos = text_end + 1
                    continue
                    
            # Check for choice pattern (3E 00 XX XX XX XX XX [choice count])
            if (start_pos < content_length - 7 and
                content[start_pos] == 0x3E and
                content[start_pos + 1] == 0x00):
                
                choice_count = content[start_pos + 7]
                current_pos = start_pos + 8
                
                for _ in range(choice_count):
                    if current_pos >= content_length:
                        break
                        
                    text_end = current_pos
                    while text_end < content_length and content[text_end] != 0:
                        text_end += 1
                    
                    if text_end < content_length:
                        text_bytes = content[current_pos:text_end]
                        text = text_bytes.decode('cp932')
                        if len(text) > 1:
                            found_texts.append({
                            'offset': start_pos,
                            'orig': text,
                            'trans': ''
                        })
                        current_pos = text_end + 1
                    else:
                        break
                        
                start_pos = current_pos
                continue
                
            start_pos += 1

        return found_texts

    def save_to_json(self, texts, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False, indent=4)

    def extract_win(self):        
        for root, _, files in os.walk(self.input_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
  
                try:
                    texts = self.extract_text(file_path)
                    if texts:
                        output_file = os.path.join(self.intermediate_dir, f'{os.path.basename(file_path)}.json')
                        self.save_to_json(texts, output_file)
                        print(f'Extracted {len(texts)} texts from {file_path}')
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

    def find_and_append(self, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        
        content_length = len(content)
        i = 0
        modified_content = bytearray(content)
        current_append_position = content_length 
        addresses_to_append = [] 

        if content[0] != 0x34:
            print("First byte is not 0x34. Exiting...")
            return

        offset = 4

        if content[offset] != 0x24:
            while content[offset] != 0x24:
                offset += 1
        # if content[offset] == 0x24:
        #     offset = offset
        # elif content[offset + 4] == 0x24:
        #     offset += 4
            

        offset += 1
        end_sequence = b'\x01\x00\x00\x00\x00\x02\x80\x02\x90'

        # Find the last occurrence of the sequence
        last_occurrence = content.rfind(end_sequence)
        if last_occurrence == -1:
            print("Sequence b'\x01\x00\x00\x00\x00\x02\x80\x02\x90' not found. Exiting...")
            return
        extracted_data = content[offset - 1:last_occurrence ]

        if not extracted_data:
            print("No data extracted. Exiting...")
            return

        extracted_data_offset = offset - 1

        # Update the content with the extracted data
        modified_content.extend(extracted_data)
        modified_content[extracted_data_offset: extracted_data_offset + 3] = struct.pack('<BH', 0x14, content_length)
        modified_content.extend(struct.pack('<BH', 0x14, last_occurrence ))
        current_append_position += len(extracted_data)
        current_append_position += 3


        while i < content_length - 2:
            if content[i] == 0x21 and content[i + 1] == 0x01 and 0 <= content[i + 2] <= 10:
                print(i)
                pattern_start = i
                start_pos = i + 3  
                
                end_pos = start_pos
                while end_pos < content_length and content[end_pos] != 0:
                    end_pos += 1
                    text_bytes = content[start_pos:end_pos]
                    
                if end_pos < content_length:
                    is_pattern1 = (end_pos + 7) < content_length and \
                                content[end_pos + 1] == 0x34 and \
                                content[end_pos + 5] == 0x25
                    is_pattern2 = (end_pos + 3) < content_length and \
                                content[end_pos + 1] == 0x25
                                
                    is_pattern3 = (end_pos + 10) < content_length and \
                                content[end_pos + 3] == 0x34 and \
                                content[end_pos + 7] == 0x25

                    if is_pattern1 or is_pattern2 or is_pattern3:
                        if is_pattern1:
                            address_pos = end_pos + 6
                        elif is_pattern2:
                            address_pos = end_pos + 2
                        else: 
                            address_pos = end_pos + 8
                        
                        if address_pos + 2 <= content_length:
                            address = struct.unpack('<H', content[address_pos:address_pos + 2])[0]
                            
                            if address <= content_length:
                                data_to_copy = content[pattern_start:address]
                                appended_address = current_append_position
                                modified_content.extend(data_to_copy)
                                
                                modified_content[pattern_start:pattern_start + 3] = struct.pack('<BH', 0x25, appended_address)

                                addresses_to_append.append((pattern_start, address))
                                
                                print(f"Moved {len(data_to_copy)} bytes from position {pattern_start} to end of file")
                                print(f"Overwritten 0x21 at {pattern_start} with appended address {appended_address}")
                                
                                current_append_position += len(data_to_copy)
                                
                                i = address  
                                continue
                    
                i = end_pos + 1  
            else:
                i += 1
        
        for _, appended_address in addresses_to_append:
            modified_content.append(0x25)
            modified_content.extend(struct.pack('<I', appended_address))
        
        return bytes(modified_content)

    def fix_files(self):
        for filename in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, filename)
            
            if os.path.isfile(file_path):
                try:
                    print(f"\nProcessing: {file_path}")
                    modified_content = self.find_and_append(file_path)
                    
                    output_path = os.path.join(self.intermediate_dir_win, filename)
                    with open(output_path, 'wb') as f:
                        f.write(modified_content)
                        
                    print(f"Modified binary saved to: {output_path}")
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

    def find_seek_address(self, content):
        for i in range(len(content) - 3):
            if content[i] == 0x14 and content[i-1] == 0x00:
                return struct.unpack('<H', content[i + 1:i + 3])[0]
        return None

    def replace_text_in_binary(self, binary_file_path, json_file_path, output_file_path):
        try:
            # Read the JSON data
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                replacements = json.load(json_file)
            
            # Read the binary file
            with open(binary_file_path, 'rb') as binary_file:
                binary_data = bytearray(binary_file.read())
            
            seek_address = self.find_seek_address(binary_data)
            if seek_address is None:
                raise ValueError("Could not find seek address")
            
            modifications = []
            search_start = seek_address
            
            for replacement in replacements:
                try:
                    replacement['trans'] = self.linebreak(replacement)
                    orig_bytes = replacement['orig'].encode('cp932')
                    trans_bytes = replacement['trans'].encode('cp932').replace(b'\n',b'\x81\x8F')
                    offset = replacement.get('offset', 'unknown')
                    trans_bytes = trans_bytes if trans_bytes else orig_bytes
                    
                    # Limit trans_bytes to original length
                    trans_bytes = trans_bytes[:len(trans_bytes)]
                    
                    found_index = None
                    for i in range(search_start, len(binary_data) - len(orig_bytes)):
                        if binary_data[i:i+len(orig_bytes)] == orig_bytes:
                            found_index = i
                            break
                    
                    if found_index is not None:
                        # Replace the text
                        binary_data[found_index:found_index+len(orig_bytes)] = trans_bytes
                        
                        # Update offset based on replacement conditions
                        if binary_data[found_index - 1] == 0x21:
                            binary_data[offset: offset + 3] = struct.pack("<BH", 0x14, found_index - 1)
                        elif binary_data[found_index - 3] == 0x21:
                            binary_data[offset: offset + 3] = struct.pack("<BH", 0x14, found_index - 3)
                        elif binary_data[found_index - 8] == 0x3E:
                            binary_data[offset: offset + 3] = struct.pack("<BH", 0x14, found_index - 8)
                        else:
                            continue
                        
                        # Track modification
                        modifications.append({
                            'original_offset': replacement.get('offset', 'Unknown'),
                            'new_offset': found_index,
                            'original_text': replacement['orig'],
                            'translated_text': replacement['trans']
                        })
                        
                        # Update search_start to continue from after this replacement
                        search_start = found_index + len(trans_bytes)
                
                except UnicodeEncodeError as e:
                    print(f"Encoding error for text: {replacement['orig']} - {e}")
            
            # Write modified binary data
            with open(output_file_path, 'wb') as output_file:
                output_file.write(binary_data)
            
            return modifications
        
        except IOError as e:
            print(f"File error: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []

    def replace_text(self):        
        all_modifications = {}
    
        files = os.listdir(self.intermediate_dir_win)
        json_files = os.listdir(self.intermediate_dir)

        for file in files:
            if file.endswith('.WIN'):
                json_file = file + '.json'
                print(json_file)
                
                if json_file in json_files:
                    binary_input_path = os.path.join(self.intermediate_dir_win, file)
                    json_input_path = os.path.join(self.intermediate_dir, json_file)
                    binary_output_path = os.path.join(self.output_dir, file)
                    
                    print(f"Processing: {file}")
                    try:
                        self.replace_text_in_binary(
                            binary_input_path, 
                            json_input_path, 
                            binary_output_path
                        )

                        print(f"Processed {file}:")
                    
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
        
        return all_modifications

    def start_replace(self):
        return self.replace_text()

    def linebreak(self, item):
        def insert_linebreaks(text, max_length = 54):
            # Ensure the text will be broken at word boundaries
            words = text.split()
            lines = []
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) + (1 if current_length > 0 else 0) > max_length:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    if current_line:
                        current_line.append(word)
                    else:
                        current_line = [word]
                    current_length += len(word) + (1 if current_length > 0 else 0)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return '\n'.join(lines)

        # Only process if translation is longer than 54 characters
        if len(item['trans']) > 54 and '\n' not in item['trans']:
            item['trans'] = insert_linebreaks(item['trans'])
        
        return item['trans']

    def read_uint32(self, handle, offset):
        handle.seek(offset)
        return struct.unpack('<I', handle.read(4))[0]
    
    def read_byte(self, handle, offset):
        handle.seek(offset)
        return handle.read(1)
    
    def read_string(self, handle, start_offset, length):
        handle.seek(start_offset)
        raw_data = handle.read(length)
        return raw_data.split(b'\x00', 1)[0].decode('cp932')

    def get_details(self):
        if not os.path.exists(self.target_dat_file):
            raise FileNotFoundError(f"Target DAT file '{self.target_dat_file}' not found.")
        
        with open(self.target_dat_file, 'rb') as f:
            # Check file signature
            if self.signature != f.read(12):
                raise Exception('Not a valid Sogna .DAT file')

            # Read file count
            file_count = self.read_uint32(f, 12)
            index_offset = 0x10

            for i in range(file_count):
                name = self.read_string(f, index_offset, 0x10)
                pos_offset = index_offset
                is_packed = self.read_byte(f, index_offset + 0x13) != b'\x00'
                size = self.read_uint32(f, index_offset + 0x14)
                unpacked_size = self.read_uint32(f, index_offset + 0x18)
                data_offset = self.read_uint32(f, index_offset + 0x1C)

                self.entry.append({
                    "name": name,
                    "pos_offset" : pos_offset,
                    "is_packed": is_packed,
                    "size": size,
                    "unpacked_size": unpacked_size,
                    "data_offset": data_offset,
                })

                index_offset += 0x20

    def patch(self):
        if not os.path.exists(self.output_dir):
            raise FileNotFoundError(f"Patch directory '{self.output_dir}' not found.")

        files = os.listdir(self.output_dir)
        matched_files = []

        with open(self.target_dat_file, 'r+b') as dat_file:
            for file in files:
                for entry in self.entry:
                    if entry['name'].strip().lower() == file.strip().lower():
                        matched_files.append(file)
                        print(f"File matched for patching: {file}")
                        file_path = os.path.join(self.output_dir, file)

                        with open(file_path, 'rb') as patch_file:
                            patch_data = patch_file.read()

                        dat_file.seek(0, os.SEEK_END)
                        new_data_offset = dat_file.tell()
                        dat_file.write(patch_data)

                        new_size = len(patch_data)
                        entry['size'] = new_size
                        entry['unpacked_size'] = new_size
                        entry['data_offset'] = new_data_offset
                        entry['is_packed'] = False 

                        dat_file.seek(entry['pos_offset'] + 0x13)  
                        dat_file.write(b'\x00')  

                        dat_file.seek(entry['pos_offset'] + 0x14)  
                        dat_file.write(struct.pack('<I', new_size))

                        dat_file.seek(entry['pos_offset'] + 0x18)  
                        dat_file.write(struct.pack('<I', new_size))

                        dat_file.seek(entry['pos_offset'] + 0x1C)
                        dat_file.write(struct.pack('<I', new_data_offset))

        if not matched_files:
            print("No matching files found for patching.")

        print(f"Total matched files: {len(matched_files)}")
