pkgname=worktimer
pkgver=1.0
pkgrel=1
pkgdesc="A simple work timer script with notifications and logging"
url="https://github.com/30be/worktimer"
arch=('any')
license=('GPL-3.0-or-later')
depends=('python' 'ffmpeg' 'pipewire-pulse' 'libnotify')
optdepends=('alacritty: for editing worklog in a terminal'
  'neovim: for editing worklog')
source=("git+$url")
b2sums=('SKIP')

package() {
  cd "$pkgname"
  install -Dm755 "src/worktimer.py" "$pkgdir/usr/bin/worktimer"
  install -Dm644 "sounds/click.ogg" "$pkgdir/usr/share/worktimer/sounds/click.ogg"
  install -Dm644 "sounds/string.ogg" "$pkgdir/usr/share/worktimer/sounds/string.ogg"
  install -Dm644 "systemd/worktimer.service" "$pkgdir/usr/lib/systemd/user/worktimer.service"
}
