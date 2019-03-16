#!//usr/bin/perl
#
# Perform MP3Val, MP3Gain, MP3Packer on a directory of files (recursively)
#
# 2013-12-15	ScottE	Initial Version
# 2014-10-25	ScottE	Remove mp3val logging
# 2018-10-20	ScottE	Add leading dot to PACKFAIL
#

use strict;
use warnings;
use File::Find;

my @mp3files;

my @mp3val = ("/usr/bin/mp3val", "-f", "-nb");
my @mp3gain = ("/usr/bin/mp3gain", "-c", "-s", "s", "-e", "-r");
my @mp3packer = ("/usr/bin/mp3packer", "-a", ".PACKFAIL", "--keep-ok", "out", "--keep-bad", "both", "-z", "-f", "-u", "--workers", "8");

sub wanted;

File::Find::find({wanted => \&wanted}, '.');
#print "$mp3files[1]\n";
#system(@mp3val,$mp3files[1]);
#system(@mp3gain,$mp3files[1]);
#system(@mp3packer,$mp3files[1]);

exit;

sub wanted {
	#/^.*\.mp3\z/s
	#&& push (@mp3files, $File::Find::name);
	if (/^.*\.mp3\z/s)
	{
		print "$_\n";
		system(@mp3val,$_);
		system(@mp3gain,$_);
		system(@mp3packer,$_);
	}
}

