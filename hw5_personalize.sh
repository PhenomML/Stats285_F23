#!/usr/bin/env bash
read -p "Enter your SU Id (Stanford login ID):" SUID
read -p "Your entry was '$SUID' : Correct SU Id? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1
for file in map_function.py main.py ; do
  sed --in-place=${file}.bak -e "s|su_ID|$SUID|g" $file
  echo "Personalization changes made to $file:"
  diff $file.bak $file
done
