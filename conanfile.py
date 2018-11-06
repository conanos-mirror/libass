from conans import ConanFile, CMake, tools
from shutil import copyfile
import os

class LibassConan(ConanFile):
    name = "libass"
    version = "0.13.7"
    description = '''libass is a portable subtitle renderer for the ASS/SSA (Advanced Substation Alpha/Substation Alpha)
    subtitle format that allows for more advanced subtitles than the conventional SRT and similar formats'''
    url = "https://github.com/conan-multimedia/libass"
    license = "BSD_like"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires = ("freetype/2.9.0@conanos/dev", "fontconfig/2.12.6@conanos/dev",
                "libpng/1.6.34@conanos/dev","fribidi/0.19.7@conanos/dev")
    source_subfolder = "source_subfolder"

    def source(self):
        tools.get('https://github.com/libass/libass/releases/download/{0}/libass-{0}.tar.gz'.format(self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        with tools.chdir(self.source_subfolder):
            with tools.environment_append({
                'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
                %(self.deps_cpp_info["freetype"].rootpath,self.deps_cpp_info["fontconfig"].rootpath,
                self.deps_cpp_info["libpng"].rootpath,self.deps_cpp_info["fribidi"].rootpath)
                }):
                self.run("autoreconf -f -i")
                _args = ["--prefix=%s/builddir"%(os.getcwd())]
                if self.options.shared:
                    _args.extend(['--enable-shared=yes','--enable-static=no'])
                else:
                    _args.extend(['--enable-shared=no','--enable-static=yes'])
                self.run('./configure %s'%(' '.join(_args)))
                self.run('make -j4')
                self.run('make install')

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

