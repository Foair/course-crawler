# Maintainer: peeweep <peeweep at 0x0 dot ee>

pkgname=('course-crawler-git')
_pkgname=course-crawler
pkgdesc="中国大学MOOC、学堂在线、网易云课堂、好大学在线、爱课程 MOOC 课程下载。"
pkgver=20181219.78aa42c
pkgrel=1
url='https://mooc.xoy.io'
arch=('any')
license=('MIT')
makedepends=('git')
depends=('python-beautifulsoup4' 'python-lxml' 'python-requests')
source=("${_pkgname}::git+https://github.com/Foair/course-crawler.git")
md5sums=('SKIP')

pkgver() {
  cd "${srcdir}/${_pkgname}"
  git log -1 --format='%cd.%h' --date=short | tr -d -
}

package() {
  cd "${srcdir}/${_pkgname}"

  install -dm755 "${pkgdir}/usr/bin"
  install -m755 "${_pkgname}.sh" "${pkgdir}/usr/bin/${_pkgname}"

  install -dm777 "${pkgdir}/usr/share/${_pkgname}"
  install -dm755 "${pkgdir}/usr/share/${_pkgname}/mooc"
  install -m755 mooc.py "${pkgdir}/usr/share/${_pkgname}/mooc.py"
  install -m755 LICENSE "${pkgdir}/usr/share/${_pkgname}/LICENSE"
  install -m755 mooc/*.py "${pkgdir}/usr/share/${_pkgname}/mooc"
}
