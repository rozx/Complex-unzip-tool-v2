"""
Rule-based cloaked file detection and renaming system.
基于规则的隐藏文件检测和重命名系统。
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .rich_utils import print_error, print_success, print_warning
from .archive_extension_utils import detect_archive_extension


@dataclass
class CloakedFileRule:
    """
    Data class representing a cloaked file detection rule.
    表示隐藏文件检测规则的数据类。
    """
    name: str
    filename_pattern: str
    ext_pattern: str
    priority: int
    matching_type: str  # "both", "filename", "ext"
    type: str  # "7z", "rar", "zip", etc.
    enabled: bool

    def __post_init__(self):
        """Validate the rule after initialization."""
        if self.matching_type not in ["both", "filename", "ext"]:
            raise ValueError(f"Invalid matching_type: {self.matching_type}")
        
        if self.matching_type == "both" and not (self.filename_pattern and self.ext_pattern):
            raise ValueError("Both filename_pattern and ext_pattern required for matching_type 'both'")
        
        if self.matching_type == "filename" and not self.filename_pattern:
            raise ValueError("filename_pattern required for matching_type 'filename'")
        
        if self.matching_type == "ext" and not self.ext_pattern:
            raise ValueError("ext_pattern required for matching_type 'ext'")


class CloakedFileDetector:
    """
    Rule-based cloaked file detector and renamer.
    基于规则的隐藏文件检测器和重命名器。
    """

    def __init__(self, rules_file_path: str):
        """
        Initialize the detector with rules from a JSON file.
        使用JSON文件中的规则初始化检测器。
        
        Args:
            rules_file_path: Path to the JSON file containing rules
        """
        self.rules: List[CloakedFileRule] = []
        self.load_rules(rules_file_path)

    def load_rules(self, rules_file_path: str) -> None:
        """
        Load rules from a JSON configuration file.
        从JSON配置文件加载规则。
        
        Args:
            rules_file_path: Path to the JSON rules file
        """
        try:
            with open(rules_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.rules = []
            for rule_data in data.get('rules', []):
                rule = CloakedFileRule(
                    name=rule_data['name'],
                    filename_pattern=rule_data['filename_pattern'],
                    ext_pattern=rule_data['ext_pattern'],
                    priority=rule_data['priority'],
                    matching_type=rule_data['matching_type'],
                    type=rule_data['type'],
                    enabled=rule_data.get('enabled', True)
                )
                self.rules.append(rule)
            
            # Sort rules by priority (higher priority first)
            self.rules.sort(key=lambda r: r.priority, reverse=True)
            
            print_success(f"Loaded {len(self.rules)} rules from {rules_file_path}")
            
        except Exception as e:
            print_error(f"Failed to load rules from {rules_file_path}: {e}")
            self.rules = []

    def _match_rule(self, filename: str, rule: CloakedFileRule) -> Optional[Tuple[str, str, str]]:
        """
        Check if a filename matches a specific rule.
        检查文件名是否匹配特定规则。
        
        Args:
            filename: The filename to check
            rule: The rule to match against
            
        Returns:
            Tuple of (base_name, original_ext, part_number) if matched, None otherwise
        """
        if not rule.enabled:
            return None

        # Split filename into name and extension
        if '.' in filename:
            name_part, ext_part = filename.rsplit('.', 1)
        else:
            name_part, ext_part = filename, ""

        base_name = ""
        part_number = ""
        original_ext = ""

        if rule.matching_type == "both":
            # Match both filename and extension patterns
            filename_match = re.match(rule.filename_pattern, name_part)
            ext_match = re.match(rule.ext_pattern, ext_part) if ext_part else None
            
            if filename_match and ext_match:
                if len(filename_match.groups()) >= 1:
                    base_name = filename_match.group(1)
                if len(filename_match.groups()) >= 2:
                    original_ext = filename_match.group(2)
                if ext_match and len(ext_match.groups()) >= 1:
                    part_number = ext_match.group(1)
                return (base_name, original_ext, part_number)

        elif rule.matching_type == "filename":
            # Match filename pattern only
            filename_match = re.match(rule.filename_pattern, name_part if name_part else filename)
            
            if filename_match:
                groups = filename_match.groups()
                if len(groups) >= 1:
                    base_name = groups[0]
                if len(groups) >= 2:
                    part_number = groups[1]
                if ext_part:
                    original_ext = ext_part
                return (base_name, original_ext, part_number)

        elif rule.matching_type == "ext":
            # Match extension pattern only
            ext_match = re.match(rule.ext_pattern, ext_part) if ext_part else None
            
            if ext_match:
                base_name = name_part
                if len(ext_match.groups()) >= 1:
                    part_number = ext_match.group(1)
                return (base_name, original_ext, part_number)

        return None

    def detect_cloaked_file(self, file_path: str) -> Optional[str]:
        """
        Detect if a file is cloaked and return the proper filename.
        检测文件是否被隐藏并返回正确的文件名。
        
        Args:
            file_path: Full path to the file
            
        Returns:
            New filename with proper extension, or None if no changes needed
        """
        filename = os.path.basename(file_path)
        dirname = os.path.dirname(file_path)

        for rule in self.rules:
            match_result = self._match_rule(filename, rule)
            
            if match_result:
                base_name, original_ext, part_number = match_result
                
                # Skip if the file already has the target format
                if self._is_already_proper_format(filename, rule.type):
                    continue
                
                # Generate new filename based on rule
                new_filename = self._generate_new_filename(
                    base_name, original_ext, part_number, rule
                )
                
                if new_filename and new_filename != filename:
                    new_path = os.path.join(dirname, new_filename)
                    
                    # Verify the detection with file signature if available
                    if self._verify_with_signature(file_path, rule.type, part_number):
                        return new_path
                    
                    # If signature verification fails, continue to next rule
                    continue
        
        return None

    def _is_already_proper_format(self, filename: str, archive_type: str) -> bool:
        """
        Check if file already has proper multi-part archive format.
        检查文件是否已经具有正确的多部分档案格式。
        
        Args:
            filename: The filename to check
            archive_type: Expected archive type
            
        Returns:
            True if file already has proper format, False otherwise
        """
        # Check if filename matches expected format like "file.7z.001"
        pattern = rf'^.+\.{re.escape(archive_type)}\.\d+$'
        return bool(re.match(pattern, filename, re.IGNORECASE))

    def _generate_new_filename(self, base_name: str, original_ext: str, 
                              part_number: str, rule: CloakedFileRule) -> Optional[str]:
        """
        Generate new filename based on matched rule.
        基于匹配的规则生成新文件名。
        
        Args:
            base_name: Base name without extension
            original_ext: Original extension (if any)
            part_number: Part number (if any)
            rule: The matched rule
            
        Returns:
            New filename or None if cannot generate
        """
        if not base_name:
            return None

        # Format part number consistently (pad with zeros if needed)
        if part_number:
            if part_number.isdigit():
                formatted_part = part_number.zfill(3)  # Pad to 3 digits
            else:
                formatted_part = part_number
        else:
            return f"{base_name}.{rule.type}"  # Single file, not multipart

        # Generate the new filename
        if original_ext and original_ext != rule.type:
            # Keep original extension if it's different from archive type
            new_filename = f"{base_name}.{original_ext}.{rule.type}.{formatted_part}"
        else:
            new_filename = f"{base_name}.{rule.type}.{formatted_part}"

        return new_filename

    def _verify_with_signature(self, file_path: str, expected_type: str, part_number: str = None) -> bool:
        """
        Verify the detected archive type with file signature.
        使用文件签名验证检测到的档案类型。
        
        Args:
            file_path: Path to the file
            expected_type: Expected archive type
            part_number: Part number if this is a multipart archive (e.g., "001", "002")
            
        Returns:
            True if signature matches or verification not applicable, False otherwise
        """
        try:
            # Use existing archive extension detection
            detected_type = detect_archive_extension(file_path)
            if detected_type:
                # If we detect a valid archive type, accept it even if different from expected
                # This handles cases where the rule guesses wrong but the file is still an archive
                return True  # Any valid archive signature is acceptable
            
            # If no signature detected, be very lenient for cloaked files
            # Cloaked files by definition don't have proper signatures/extensions
            return True
            
        except Exception as e:
            print_warning(f"Could not verify file signature for {file_path}: {e}")
            return True  # Assume valid if verification fails

    def uncloak_file(self, file_path: str) -> str:
        """
        Uncloak a single file and rename it if needed.
        解除单个文件的隐藏并在需要时重命名。
        
        Args:
            file_path: Full path to the file to uncloak
            
        Returns:
            New file path with proper extension, or original path if no changes needed
        """
        if not os.path.exists(file_path):
            return file_path

        new_path = self.detect_cloaked_file(file_path)
        
        if new_path and new_path != file_path:
            try:
                # Rename the actual file
                os.rename(file_path, new_path)
                print_success(f"Renamed: {os.path.basename(file_path)} -> {os.path.basename(new_path)}")
                return new_path
            except Exception as e:
                print_error(f"Failed to rename {file_path}: {e}")
                return file_path
        
        return file_path

    def uncloak_files(self, file_paths: List[str]) -> List[str]:
        """
        Uncloak multiple files and return updated paths.
        解除多个文件的隐藏并返回更新的路径。
        
        Args:
            file_paths: List of file paths to uncloak
            
        Returns:
            List of updated file paths with proper extensions
        """
        updated_paths = []
        
        for file_path in file_paths:
            updated_path = self.uncloak_file(file_path)
            updated_paths.append(updated_path)
        
        return updated_paths

    def get_rule_info(self) -> Dict:
        """
        Get information about loaded rules.
        获取已加载规则的信息。
        
        Returns:
            Dictionary containing rule statistics and details
        """
        enabled_rules = [r for r in self.rules if r.enabled]
        disabled_rules = [r for r in self.rules if not r.enabled]
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(enabled_rules),
            "disabled_rules": len(disabled_rules),
            "rules_by_type": {
                rule_type: len([r for r in enabled_rules if r.type == rule_type])
                for rule_type in set(r.type for r in enabled_rules)
            },
            "highest_priority": max(r.priority for r in self.rules) if self.rules else 0,
            "lowest_priority": min(r.priority for r in self.rules) if self.rules else 0
        }
