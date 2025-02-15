git add -A
git commit
git push
cd build || exit
meson compile
cp worktimer ~
