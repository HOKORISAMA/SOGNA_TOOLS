import os
import struct
import click

class PackedEntry:
    def __init__(self, name, is_packed, size, unpacked_size, offset):
        self.name = name
        self.is_packed = is_packed
        self.size = size
        self.unpacked_size = unpacked_size
        self.offset = offset

def read_string(file, offset, length):
    file.seek(offset)
    return file.read(length).decode('ascii').strip('\x00')

def read_uint32(file, offset):
    file.seek(offset)
    return struct.unpack('<I', file.read(4))[0]

def read_uint16(file):
    return struct.unpack('<H', file.read(2))[0]

def lz_unpack(input_file, output, unpacked_size):
    dst = 0
    bits = 0
    mask = 0
    while dst < unpacked_size:
        mask >>= 1
        if mask == 0:
            bits = input_file.read(1)[0]
            if bits == -1:
                break
            mask = 0x80
        if (mask & bits) != 0:
            offset = read_uint16(input_file)
            count = (offset >> 12) + 1
            offset &= 0xFFF
            for i in range(count):
                output[dst] = output[dst - offset]
                dst += 1
        else:
            output[dst] = input_file.read(1)[0]
            dst += 1

def try_open(file_path):
    with open(file_path, 'rb') as file:
        file.seek(4)
        if file.read(8) != b'DAT 1.00':
            return None
        count = read_uint32(file, 12)
        index_offset = 0x10
        dir_entries = []
        for _ in range(count):
            name = read_string(file, index_offset, 0x10)
            is_packed = file.read(1)[0] != 0
            size = read_uint32(file, index_offset + 0x14)
            unpacked_size = read_uint32(file, index_offset + 0x18)
            offset = read_uint32(file, index_offset + 0x1C)
            entry = PackedEntry(name, is_packed, size, unpacked_size, offset)
            dir_entries.append(entry)
            index_offset += 0x20
        return dir_entries

def open_entry(file_path, entry):
    with open(file_path, 'rb') as file:
        file.seek(entry.offset)
        if not entry.is_packed:
            return file.read(entry.size)
        output = bytearray(entry.unpacked_size)
        lz_unpack(file, output, entry.unpacked_size)
        return output

@click.command()
@click.argument('directory')
@click.argument('archive')
def main(directory, archive):
    dir_entries = try_open(archive)
    if not dir_entries:
        click.echo(f"Failed to open archive: {archive}")
        return

    for entry in dir_entries:
        output_path = os.path.join(directory, entry.name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as output_file:
            data = open_entry(archive, entry)
            output_file.write(data)
        click.echo(f"Extracted: {entry.name}")

if __name__ == "__main__":
    main()
