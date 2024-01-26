cd ./var

rmdir game_primary
rmdir game_secondary_1
rmdir game_secondary_2

sudo umount ./var/game_primary/mount
sudo umount ./var/game_secondary_1/mount
sudo umount ./var/game_secondary_2/mount

mkdir game_primary
mkdir game_secondary_1
mkdir game_secondary_2

cd game_primary/
mkdir data
mkdir mount
cd ..
cd game_secondary_1
mkdir data
mkdir mount

cd ..
cd game_secondary_2
mkdir data
mkdir mount


sudo umount ./var/game_primary/mount
sudo umount ./var/game_secondary_1/mount
sudo umount ./var/game_secondary_2/mount
