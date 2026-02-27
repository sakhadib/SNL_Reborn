"""
Binary Game Storage - SARG Binary Game Format v1.0
Implements the storage specification from GameStoragePrinciple.md
"""

import struct
from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path

# Constants from specification
MAGIC_NUMBER = b'SARG'
FORMAT_VERSION = 1
BOARD_VERSION = 1

# File structure sizes (in bytes)
FILE_HEADER_SIZE = 16
GAME_HEADER_SIZE = 16
MOVE_SIZE = 2


@dataclass
class FileHeader:
    """File header (16 bytes)."""
    magic: bytes  # 4 bytes: b'SARG'
    format_version: int  # 1 byte
    board_version: int  # 1 byte
    # reserved: 10 bytes
    
    def to_bytes(self) -> bytes:
        """Encode file header to bytes."""
        return struct.pack(
            '4s B B 10x',  # 4s=4 byte string, B=unsigned byte, 10x=10 padding bytes
            self.magic,
            self.format_version,
            self.board_version
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'FileHeader':
        """Decode file header from bytes."""
        if len(data) != FILE_HEADER_SIZE:
            raise ValueError(f"Invalid file header size: {len(data)}")
        
        magic, format_ver, board_ver = struct.unpack('4s B B 10x', data)
        return cls(magic=magic, format_version=format_ver, board_version=board_ver)
    
    @classmethod
    def default(cls) -> 'FileHeader':
        """Create default file header."""
        return cls(
            magic=MAGIC_NUMBER,
            format_version=FORMAT_VERSION,
            board_version=BOARD_VERSION
        )
    
    def validate(self) -> None:
        """Validate file header."""
        if self.magic != MAGIC_NUMBER:
            raise ValueError(f"Invalid magic number: {self.magic}")
        if self.format_version != FORMAT_VERSION:
            raise ValueError(f"Unsupported format version: {self.format_version}")


@dataclass
class GameHeader:
    """Game header (16 bytes)."""
    player_a_id: int  # 1 byte
    player_b_id: int  # 1 byte
    winner: int  # 1 byte: 0=Player A, 1=Player B
    move_count: int  # 2 bytes: unsigned short
    # reserved: 11 bytes
    
    def to_bytes(self) -> bytes:
        """Encode game header to bytes."""
        return struct.pack(
            'B B B H 11x',  # B=unsigned byte, H=unsigned short, 11x=11 padding
            self.player_a_id,
            self.player_b_id,
            self.winner,
            self.move_count
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'GameHeader':
        """Decode game header from bytes."""
        if len(data) != GAME_HEADER_SIZE:
            raise ValueError(f"Invalid game header size: {len(data)}")
        
        a_id, b_id, winner, move_count = struct.unpack('B B B H 11x', data)
        return cls(
            player_a_id=a_id,
            player_b_id=b_id,
            winner=winner,
            move_count=move_count
        )


@dataclass
class Move:
    """
    Single move encoding (2 bytes).
    
    Byte 1:
      Bits 0-2: dice1 (3 bits, values 1-6)
      Bits 3-5: dice2 (3 bits, values 1-6)
      Bits 6-7: action (2 bits, 0-2)
    Byte 2:
      Bits 0-7: reserved
    """
    dice1: int  # 1-6
    dice2: int  # 1-6
    action: int  # 0=choose_die_1, 1=choose_die_2, 2=skip
    
    def to_bytes(self) -> bytes:
        """Encode move to 2 bytes."""
        # Validate values
        if not (1 <= self.dice1 <= 6):
            raise ValueError(f"Invalid dice1: {self.dice1}")
        if not (1 <= self.dice2 <= 6):
            raise ValueError(f"Invalid dice2: {self.dice2}")
        if not (0 <= self.action <= 2):
            raise ValueError(f"Invalid action: {self.action}")
        
        # Encode into byte 1
        # Store dice as 0-5 (subtract 1) to fit in 3 bits
        byte1 = (self.dice1 - 1) | ((self.dice2 - 1) << 3) | (self.action << 6)
        byte2 = 0  # Reserved
        
        return struct.pack('B B', byte1, byte2)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Move':
        """Decode move from 2 bytes."""
        if len(data) != MOVE_SIZE:
            raise ValueError(f"Invalid move size: {len(data)}")
        
        byte1, byte2 = struct.unpack('B B', data)
        
        # Extract fields from byte 1
        dice1 = (byte1 & 0b00000111) + 1  # Bits 0-2, add 1 to get 1-6
        dice2 = ((byte1 >> 3) & 0b00000111) + 1  # Bits 3-5, add 1 to get 1-6
        action = (byte1 >> 6) & 0b00000011  # Bits 6-7
        
        return cls(dice1=dice1, dice2=dice2, action=action)


@dataclass
class GameRecord:
    """Complete game record with header and moves."""
    header: GameHeader
    moves: List[Move]
    
    def to_bytes(self) -> bytes:
        """Encode complete game to bytes."""
        data = self.header.to_bytes()
        for move in self.moves:
            data += move.to_bytes()
        return data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'GameRecord':
        """Decode complete game from bytes."""
        if len(data) < GAME_HEADER_SIZE:
            raise ValueError("Data too short for game header")
        
        # Parse header
        header = GameHeader.from_bytes(data[:GAME_HEADER_SIZE])
        
        # Parse moves
        moves = []
        offset = GAME_HEADER_SIZE
        expected_size = GAME_HEADER_SIZE + header.move_count * MOVE_SIZE
        
        if len(data) != expected_size:
            raise ValueError(
                f"Invalid game size: expected {expected_size}, got {len(data)}"
            )
        
        for _ in range(header.move_count):
            move_data = data[offset:offset + MOVE_SIZE]
            moves.append(Move.from_bytes(move_data))
            offset += MOVE_SIZE
        
        return cls(header=header, moves=moves)
    
    def get_size(self) -> int:
        """Get total size in bytes."""
        return GAME_HEADER_SIZE + len(self.moves) * MOVE_SIZE


class GameStorage:
    """
    Binary game storage handler.
    Manages reading and writing games in SARG Binary Format v1.0
    """
    
    def __init__(self, filepath: Path):
        """Initialize storage with filepath."""
        self.filepath = Path(filepath)
        self.file_header = FileHeader.default()
    
    def write_file_header(self) -> None:
        """Write file header (only once at file creation)."""
        with open(self.filepath, 'wb') as f:
            f.write(self.file_header.to_bytes())
    
    def append_game(self, game_record: GameRecord) -> int:
        """
        Append game to storage file.
        Returns byte offset where game was written.
        """
        # Ensure file exists with header
        if not self.filepath.exists():
            self.write_file_header()
        
        # Get current file size (offset for this game)
        offset = self.filepath.stat().st_size
        
        # Append game
        with open(self.filepath, 'ab') as f:
            f.write(game_record.to_bytes())
        
        return offset
    
    def read_file_header(self) -> FileHeader:
        """Read and validate file header."""
        with open(self.filepath, 'rb') as f:
            data = f.read(FILE_HEADER_SIZE)
            header = FileHeader.from_bytes(data)
            header.validate()
            return header
    
    def read_game_at_offset(self, offset: int) -> GameRecord:
        """Read game at specific byte offset."""
        with open(self.filepath, 'rb') as f:
            # Seek to game position
            f.seek(offset)
            
            # Read game header
            header_data = f.read(GAME_HEADER_SIZE)
            if len(header_data) != GAME_HEADER_SIZE:
                raise ValueError("Could not read game header")
            
            header = GameHeader.from_bytes(header_data)
            
            # Read moves
            moves_data = f.read(header.move_count * MOVE_SIZE)
            if len(moves_data) != header.move_count * MOVE_SIZE:
                raise ValueError("Could not read all moves")
            
            # Parse moves
            moves = []
            for i in range(header.move_count):
                move_offset = i * MOVE_SIZE
                move_data = moves_data[move_offset:move_offset + MOVE_SIZE]
                moves.append(Move.from_bytes(move_data))
            
            return GameRecord(header=header, moves=moves)
    
    def iter_games(self):
        """Iterate over all games in file."""
        with open(self.filepath, 'rb') as f:
            # Skip file header
            f.seek(FILE_HEADER_SIZE)
            
            while True:
                # Try to read game header
                header_data = f.read(GAME_HEADER_SIZE)
                if not header_data or len(header_data) < GAME_HEADER_SIZE:
                    break
                
                header = GameHeader.from_bytes(header_data)
                
                # Read moves
                moves_data = f.read(header.move_count * MOVE_SIZE)
                if len(moves_data) != header.move_count * MOVE_SIZE:
                    raise ValueError("Incomplete game data")
                
                # Parse moves
                moves = []
                for i in range(header.move_count):
                    move_offset = i * MOVE_SIZE
                    move_data = moves_data[move_offset:move_offset + MOVE_SIZE]
                    moves.append(Move.from_bytes(move_data))
                
                yield GameRecord(header=header, moves=moves)
    
    def count_games(self) -> int:
        """Count total games in file."""
        return sum(1 for _ in self.iter_games())
    
    def get_file_size(self) -> int:
        """Get storage file size in bytes."""
        if not self.filepath.exists():
            return 0
        return self.filepath.stat().st_size
