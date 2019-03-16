# PowerShell script to validate, pack, replaygain MP3 files
#
# Takes directory with mp3 files as argument, defaults to "."
$MP3Tools = "C:\Program Files (x86)\MP3Gain\"

$MP3Val = $MP3Tools + "MP3Val.exe"
$MP3ValArgs = "-f -nb -lmp3val_log.txt"

$MP3Packer = $MP3Tools + "mp3packer.exe"
$MP3PackerArgs = '-a "PACKFAIL" --keep-ok "out" --keep-bad "both" -z -u -f'

$MP3Gain = $MP3Tools + "mp3gain.exe"
$MP3GainArgs = "/r /s s /t /k"

if ($args[0])
{
	$MP3Path = $args[0]
}
else
{
	$MP3Path = "."
}

# Print SOMETHING, so we know we're working
Write-Host "Fixing files in $MP3Path"

# Find all files below the $MP3Path directory
Foreach ($file in Get-Childitem $MP3Path -recurse -force)
{
	# Only operate on files that are named .mp3 (case insensitive)
	if ($file.Extension -eq ".mp3")
	{
		$MyFile = '"' + $file.DirectoryName + "\" + $file.Name + '"'
		$MyArgs = $MyFile + " " + $MP3ValArgs

		Write-Host ""
		Write-Host $MyFile

		Write-Host "Validating " -nonewline
		Start-Process -FilePath $MP3Val -ArgumentList $MyArgs -Wait -WindowStyle Hidden

		$MyArgs = $MP3GainArgs + " " + $MyFile
		Write-Host "ReplayGaining " -nonewline
		Start-Process -FilePath $MP3Gain -ArgumentList $MyArgs -Wait -WindowStyle Hidden

		$MyArgs = $MyFile + " " + $MP3PackerArgs
		Write-Host "Packing " -nonewline
		Start-Process -FilePath $MP3Packer -ArgumentList $MyArgs -Wait -WindowStyle Hidden
	}
}

# Look at all files below $MP3Path again for ones that failed re-packing
Foreach ($file in Get-Childitem $MP3Path -recurse -force)
{
	if ($file.Name -match "PACKFAIL")
	{
		$MyFile = '"' + $file.DirectoryName + "\" + $file.Name + '"'
		Write-Host $MyFile
	}
}