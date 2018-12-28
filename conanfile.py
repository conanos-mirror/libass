from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil

class LibassConan(ConanFile):
    name = "libass"
    version = "0.14.0-13"
    description = 'libass is a portable subtitle renderer for the ASS/SSA (Advanced Substation Alpha/Substation Alpha) subtitle format'
    url = "https://github.com/conanos/libass"
    homepage = 'https://github.com/libass'
    license = "ISC"
    patch = "msvc-link-library-normalize.patch"
    exports = ["COPYING", patch]
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def requirements(self):
        self.requires.add("freetype/2.9.1@conanos/stable")
        self.requires.add("fontconfig/2.13.0@conanos/stable")
        self.requires.add("libpng/1.6.34@conanos/stable")
        self.requires.add("fribidi/1.0.5@conanos/stable")

    def build_requirements(self):
        self.build_requires("libiconv/1.15@conanos/stable")
        self.build_requires("harfbuzz/2.1.3@conanos/stable")
        self.build_requires("fribidi/1.0.5@conanos/stable")


    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/libass/archive/{version}.tar.gz'
        tools.get(url_.format(version=self.version))
        if self.settings.os == 'Windows':
            tools.patch(patch_file=self.patch)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        #with tools.chdir(self.source_subfolder):
        #    with tools.environment_append({
        #        'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig:%s/lib/pkgconfig"
        #        %(self.deps_cpp_info["freetype"].rootpath,self.deps_cpp_info["fontconfig"].rootpath,
        #        self.deps_cpp_info["libpng"].rootpath,self.deps_cpp_info["fribidi"].rootpath)
        #        }):
        #        self.run("autoreconf -f -i")
        #        _args = ["--prefix=%s/builddir"%(os.getcwd())]
        #        if self.options.shared:
        #            _args.extend(['--enable-shared=yes','--enable-static=no'])
        #        else:
        #            _args.extend(['--enable-shared=no','--enable-static=yes'])
        #        self.run('./configure %s'%(' '.join(_args)))
        #        self.run('make -j4')
        #        self.run('make install')
        include = [ os.path.join(self.deps_cpp_info[i].rootpath, "include", i) for i in ["harfbuzz","fribidi"] ]
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                with tools.environment_append({
                    "INCLUDE" : os.pathsep.join(include + [os.getenv('INCLUDE')]),
                    }):
                    msbuild = MSBuild(self)
                    build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                    msbuild.build("libass.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))
            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copy(os.path.join(self.build_folder,self._source_subfolder,"libass.pc.in"),
                        os.path.join(self.package_folder,"lib","pkgconfig","libass.pc"))
            lib = "-lassd" if self.options.shared else "-lass"
            replacements = {
                "@prefix@"          : self.package_folder,
                "@exec_prefix@"     : "${prefix}/lib",
                "@libdir@"          : "${prefix}/lib",
                "@includedir@"      : "${prefix}/include",
                "@PACKAGE_VERSION@" : self.version,
                "@PKG_REQUIRES_DEFAULT@" : "",
                "@PKG_REQUIRES_PRIVATE@" : "harfbuzz, fontconfig, fribidi, freetype2",
                "@PKG_LIBS_DEFAULT@"     : "",
                "@PKG_LIBS_PRIVATE@"     : "-liconv",
                "-lass"                  : lib
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig","libass.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

