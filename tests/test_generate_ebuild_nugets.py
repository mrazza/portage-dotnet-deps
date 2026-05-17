import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
import subprocess

# Add the parent directory to sys.path to import the script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generate_ebuild_nugets import get_nugets, format_nugets_block, update_ebuild

def test_format_nugets_block_empty():
    assert format_nugets_block([]) == 'NUGETS=""'

def test_format_nugets_block_with_items():
    nugets = ["package1@1.0.0", "package2@2.0.0"]
    expected = 'NUGETS="\n    package1@1.0.0\n    package2@2.0.0\n"'
    assert format_nugets_block(nugets) == expected

@patch('subprocess.run')
@patch('os.walk')
@patch('builtins.open', new_callable=mock_open)
def test_get_nugets(mock_file, mock_walk, mock_run):
    # Mock subprocess.run for dotnet restore
    mock_run.return_value = MagicMock(returncode=0)
    
    # Mock os.walk to find project.assets.json
    mock_walk.return_value = [
        ('/fake/path/obj', [], ['project.assets.json'])
    ]
    
    # Mock json data in project.assets.json
    assets_data = {
        "libraries": {
            "Package.Name/1.2.3": {"type": "package"},
            "Other.Lib/4.5.6": {"type": "package"},
            "Some.Project/1.0.0": {"type": "project"}
        }
    }
    mock_file.return_value.read.return_value = json.dumps(assets_data)
    
    result = get_nugets("/fake/path")
    
    assert "package.name@1.2.3" in result
    assert "other.lib@4.5.6" in result
    assert "some.project@1.0.0" not in result
    assert len(result) == 2
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_get_nugets_restore_fails(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, ["dotnet", "restore"], stderr=b"Restore failed")
    
    with pytest.raises(SystemExit) as e:
        get_nugets("/fake/path")
    assert e.value.code == 1

@patch('subprocess.run')
@patch('os.walk')
def test_get_nugets_no_assets(mock_walk, mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    mock_walk.return_value = [('/fake/path', [], [])]
    
    with pytest.raises(SystemExit) as e:
        get_nugets("/fake/path")
    assert e.value.code == 1

@patch('os.path.exists')
def test_update_ebuild_file_not_found(mock_exists):
    mock_exists.return_value = False
    with pytest.raises(SystemExit) as e:
        update_ebuild('nonexistent.ebuild', 'block')
    assert e.value.code == 1

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='inherit dotnet-pkg\n')
def test_update_ebuild_new(mock_file, mock_exists):
    mock_exists.return_value = True
    nugets_block = 'NUGETS="\n    pkg@1.0.0\n"'
    
    update_ebuild('test.ebuild', nugets_block)
    
    # Check if it inserted before inherit
    written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
    assert 'NUGETS="\n    pkg@1.0.0\n"\n\ninherit dotnet-pkg' in written_data

@patch('os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='NUGETS="\n    old@1.0.0\n"\ninherit dotnet-pkg\n')
def test_update_ebuild_update(mock_file, mock_exists):
    mock_exists.return_value = True
    nugets_block = 'NUGETS="\n    new@2.0.0\n"'
    
    update_ebuild('test.ebuild', nugets_block)
    
    written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
    assert 'NUGETS="\n    new@2.0.0\n"' in written_data
    assert 'old@1.0.0' not in written_data
