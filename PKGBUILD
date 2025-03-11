pkgname=worktimer
pkgver=1.0
pkgrel=1
pkgdesc="A simple work timer script with notifications and logging"
arch=('any')
license=('unknown')
depends=('python' 'ffmpeg' 'pipewire-pulse' 'libnotify')
optdepends=('alacritty: for editing worklog in a terminal'
  'neovim: for editing worklog')
source=("src/worktimer" "sounds/click.ogg" "sounds/string.ogg" "systemd/worktimer.service")
md5sums=('SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
  install -Dm755 "src/worktimer" "$pkgdir/usr/bin/worktimer"
  install -Dm644 "sounds/click.ogg" "$pkgdir/usr/share/worktimer/sounds/click.ogg"
  install -Dm644 "sounds/string.ogg" "$pkgdir/usr/share/worktimer/sounds/string.ogg"
  install -Dm644 "systemd/worktimer.service" "$pkgdir/usr/lib/systemd/user/worktimer.service"
}
