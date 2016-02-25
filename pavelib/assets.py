"""
Asset compilation and collection.
"""

from __future__ import print_function
from datetime import datetime
import argparse
import glob
import traceback

from paver import tasks
from paver.easy import sh, path, task, cmdopts, needs, consume_args, call_task, no_help
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from .utils.envs import Env
from .utils.cmd import cmd, django_cmd

# setup baseline paths

ALL_SYSTEMS = ['lms', 'studio']
COFFEE_DIRS = ['lms', 'cms', 'common']

LMS = 'lms'
CMS = 'cms'

SYSTEMS = {
    'lms': LMS,
    'cms': CMS,
    'studio': CMS
}

# Common lookup paths that are added to the lookup paths for all sass compilations
COMMON_LOOKUP_DIRS = [
    path("common/static"),
    path("common/static/sass"),
]

# system specific lookup path additions, add sass dirs if one system depends on the sass files for other systems
SASS_LOOKUP_DEPENDENCIES = {
    'cms': [path('lms') / 'static' / 'sass' / 'partials', ],
}

THEME_SASS_WATCHER_DIRS = []


def get_sass_directories(system, theme_dir):
    """
    Determine the set of SASS directories to be compiled for the specified list of system and theme
    and return a list of those directories.

    Each item in the list is dict object containing the following key-value pairs.
    {
        "sass_source_dir": "",  # directory where source sass files are present
        "css_destination_dir": "",  # destination where css files would be placed
        "lookup_paths": [],  # list of directories to be passed as lookup paths for @import resolution.
    }

    if theme_dir is empty or None then return sass directories for the given system only. (i.e. lms or cms)

    :param system: name if the system for which to compile sass e.g. 'lms', 'cms'
    :param theme_dir: absolute path of theme for which to compile sass files.
    """
    if system not in SYSTEMS:
        raise ValueError("'system' must be one of ({allowed_values})".format(allowed_values=', '.join(SYSTEMS.keys())))
    system = SYSTEMS[system]

    applicable_directories = list()

    # add common sass directories
    applicable_directories.append({
        "sass_source_dir": path("common/static/sass"),
        "css_destination_dir": path("common/static/css"),
        "lookup_paths": [
            path("common/static"),
            path("common/static/sass"),
        ],
    })

    if theme_dir:
        # Add theme sass directories
        applicable_directories.extend(
            get_theme_sass_dirs(system, theme_dir)
        )
    else:
        # add system sass directories
        applicable_directories.extend(
            get_system_sass_dirs(system)
        )

    return applicable_directories


def get_theme_sass_dirs(system, theme_dir):
    """
    Return list of sass dirs that need to be compiled for the given theme. Also add theme sass directories to
    THEME_SASS_WATCHER_DIRS variables so that they could be added to sass watcher later.

    :param system: name if the system for which to compile sass e.g. 'lms', 'cms'
    :param theme_dir: absolute path of theme for which to compile sass files.
    """
    if system not in ('lms', 'cms'):
        raise ValueError('"system" must either be "lms" or "cms"')

    dirs = []

    system_sass = path(system) / "static" / "sass"
    sass = theme_dir / system / "static" / "sass"
    css = theme_dir / system / "static" / "css"

    if sass.isdir():
        css.mkdir_p()

        # first compile lms sass files and place css in theme dir
        dirs.append({
            "sass_source_dir": system_sass,
            "css_destination_dir": css,
            "lookup_paths": [
                sass / "partials",
                system_sass / "partials",
                system_sass,
            ],
        })

        # now compile theme sass files and override css files generated from lms
        dirs.append({
            "sass_source_dir": sass,
            "css_destination_dir": css,
            "lookup_paths": [
                sass / "partials",
                system_sass / "partials",
                system_sass,
            ],
        })

        # Add theme dirs to sass watcher directories
        THEME_SASS_WATCHER_DIRS.extend([sass, sass / 'partials'])

    return dirs


def get_system_sass_dirs(system):
    """
    Return list of sass dirs that need to be compiled for the given system.

    :param system: name if the system for which to compile sass e.g. 'lms', 'cms'
    """
    if system not in ('lms', 'cms'):
        raise ValueError('"system" must either be "lms" or "cms"')

    dirs = []
    sass = path(system) / "static" / "sass"
    css = path(system) / "static" / "css"

    dependencies = SASS_LOOKUP_DEPENDENCIES.get(system, [])
    dirs.append({
        "sass_source_dir": sass,
        "css_destination_dir": css,
        "lookup_paths": dependencies + [
            sass / "partials",
            sass,
        ],
    })

    if system == 'lms':
        dirs.append({
            "sass_source_dir": path(system) / "static" / "certificates" / "sass",
            "css_destination_dir": path(system) / "static" / "certificates" / "css",
            "lookup_paths": [
                sass / "partials",
                sass
            ],
        })

    return dirs


def get_watcher_dirs():
    """
    :return dirs that need to be added to sass watchers.
    """
    dirs = []
    dirs.extend(COMMON_LOOKUP_DIRS)
    dirs.extend(THEME_SASS_WATCHER_DIRS)
    for _dir in get_sass_directories('lms', None) + get_sass_directories('cms', None):
        dirs.append(_dir['sass_source_dir'])
        dirs.extend(_dir['lookup_paths'])
    return dirs


class CoffeeScriptWatcher(PatternMatchingEventHandler):
    """
    Watches for coffeescript changes
    """
    ignore_directories = True
    patterns = ['*.coffee']

    def register(self, observer):
        """
        register files with observer
        """
        dirnames = set()
        for filename in sh(coffeescript_files(), capture=True).splitlines():
            dirnames.add(path(filename).dirname())
        for dirname in dirnames:
            observer.schedule(self, dirname)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_coffeescript(event.src_path)
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()


class SassWatcher(PatternMatchingEventHandler):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    patterns = ['*.scss']
    ignore_patterns = ['common/static/xmodule/*']

    def register(self, observer):
        """
        register files with observer
        """
        for dirname in get_watcher_dirs():
            paths = []
            if '*' in dirname:
                paths.extend(glob.glob(dirname))
            else:
                paths.append(dirname)
            for dirname in paths:
                observer.schedule(self, dirname, recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_sass()      # pylint: disable=no-value-for-parameter
        except Exception:       # pylint: disable=broad-except
            traceback.print_exc()


class XModuleSassWatcher(SassWatcher):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    ignore_patterns = []

    def register(self, observer):
        """
        register files with observer
        """
        observer.schedule(self, 'common/lib/xmodule/', recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()


class XModuleAssetsWatcher(PatternMatchingEventHandler):
    """
    Watches for css and js file changes
    """
    ignore_directories = True
    patterns = ['*.css', '*.js']

    def register(self, observer):
        """
        Register files with observer
        """
        observer.schedule(self, 'common/lib/xmodule/', recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()

        # To refresh the hash values of static xmodule content
        restart_django_servers()


def coffeescript_files():
    """
    return find command for paths containing coffee files
    """
    dirs = " ".join(Env.REPO_ROOT / coffee_dir for coffee_dir in COFFEE_DIRS)
    return cmd('find', dirs, '-type f', '-name \"*.coffee\"')


@task
@no_help
def compile_coffeescript(*files):
    """
    Compile CoffeeScript to JavaScript.
    """
    if not files:
        files = ["`{}`".format(coffeescript_files())]
    sh(cmd(
        "node_modules/.bin/coffee", "--compile", *files
    ))


@task
@no_help
@cmdopts([
    ('system=', 's', 'The system to compile sass for (defaults to all)'),
    ('themes_dir=', '-td', 'The themes dir containing all themes (defaults to None)'),
    ('themes=', '-t', 'The theme to compile sass for (defaults to None)'),
    ('debug', 'd', 'Debug mode'),
    ('force', '', 'Force full compilation'),
])
def compile_sass(options):
    """
    Compile Sass to CSS. following is a list of some possible ways to use this command.

    Command:
        1. paver compile_sass
    Description:
        compile sass files for both lms and cms

    Command:
        1. paver compile_sass --themes_dir=/edx/app/edxapp/edx-platform/themes --themes=red-theme
    Description:
        compile sass files for both lms and cms for 'red-theme' present in '/edx/app/edxapp/edx-platform/themes'

    Command:
        1. paver compile_sass --themes_dir=/edx/app/edxapp/edx-platform/themes --themes=red-theme,stanford-style
    Description:
        compile sass files for both lms and cms for 'red-theme' and 'stanford-style' present in
        '/edx/app/edxapp/edx-platform/themes'.

    Command:
      paver compile_sass --system=cms --themes_dir=/edx/app/edxapp/edx-platform/themes --themes=red-theme,stanford-style
    Description:
        compile sass files for cms only for 'red-theme' and 'stanford-style' present in
        '/edx/app/edxapp/edx-platform/themes'.

    """
    debug = options.get('debug')
    force = options.get('force')
    systems = getattr(options, 'system', ALL_SYSTEMS)
    themes = getattr(options, 'themes', None)
    themes_dir = getattr(options, 'themes_dir', None)

    if not themes_dir and themes:
        # We can not compile a theme sass without knowing the directory that contains the theme.
        raise ValueError('themes_dir must be provided for compiling theme sass.')
    else:
        theme_base_dir = path(themes_dir)

    if isinstance(systems, basestring):
        systems = systems.split(',')
    else:
        systems = systems if isinstance(systems, list) else [systems]
    if isinstance(themes, basestring):
        themes = themes.split(',')
    else:
        themes = themes if isinstance(themes, list) else [themes]

    timing_info = []
    dry_run = tasks.environment.dry_run
    compilation_results = {'success': [], 'failure': []}

    print("\t\tStarted compiling Sass:")
    for system in systems:
        for theme in themes:
            print("Started compiling '{system}' Sass for '{theme}'.".format(system=system, theme=theme or 'system'))

            # Compile sass files
            is_successful = _compile_sass(
                system=system,
                theme=theme_base_dir / theme if theme_base_dir and theme else None,
                debug=debug,
                force=force,
                timing_info=timing_info
            )

            if is_successful:
                print("Finished compiling '{system}' Sass for '{theme}'.".format(
                    system=system, theme=theme or 'system'
                ))

            compilation_results['success' if is_successful else 'failure'].append('{system} sass for {theme}.'.format(
                system=system, theme=theme or 'system',
            ))

    print("\t\tFinished compiling Sass:")
    if not dry_run:
        for sass_dir, css_dir, duration in timing_info:
            print(">> {} -> {} in {}s".format(sass_dir, css_dir, duration))

    if compilation_results['success']:
        print("\033[92m\n\nSuccessful compilations:\n--- " + "\n--- ".join(compilation_results['success']) + "\033[00m")
    if compilation_results['failure']:
        print("\033[91m\n\nFailed compilations:\n--- " + "\n--- ".join(compilation_results['failure']) + "\033[00m")


def _compile_sass(system, theme, debug, force, timing_info):
    """
    Compile sass files for the given system and theme.

    :param system: system to compile sass for e.g. 'lm', 'cms'
    :param theme: absolute path of the theme to compile sass for.
    :param debug:
    :param force:
    """

    # Note: import sass only when it is needed and not at the top of the file.
    # This allows other paver commands to operate even without libsass being
    # installed. In particular, this allows the install_prereqs command to be
    # used to install the dependency.
    import sass
    sass_dirs = get_sass_directories(system, theme)

    dry_run = tasks.environment.dry_run

    # determine css out put style and source comments enabling
    if debug:
        source_comments = True
        output_style = 'nested'
    else:
        source_comments = False
        output_style = 'compressed'

    for dirs in sass_dirs:
        start = datetime.now()
        css_dir = dirs['css_destination_dir']
        system_sass_dir = dirs['sass_source_dir']
        lookup_paths = dirs['lookup_paths']

        if not system_sass_dir.isdir():
            print("\033[91m Sass dir '{dir}' does not exists, skipping sass compilation for '{theme}' \033[00m".format(
                dir=sass_dirs, theme=theme or system,
            ))
            # invalid sass directory, skip sass compilation
            continue

        if force:
            if dry_run:
                tasks.environment.info("rm -rf {css_dir}/*.css".format(
                    css_dir=css_dir,
                ))
            else:
                sh("rm -rf {css_dir}/*.css".format(css_dir=css_dir))

        if dry_run:
            tasks.environment.info("libsass {sass_dir}".format(
                sass_dir=system_sass_dir,
            ))
        else:
            sass.compile(
                dirname=(system_sass_dir, css_dir),
                include_paths=COMMON_LOOKUP_DIRS + lookup_paths,
                source_comments=source_comments,
                output_style=output_style,
            )
            duration = datetime.now() - start
            timing_info.append((system_sass_dir, css_dir, duration))
    return True


def compile_templated_sass(systems, settings):
    """
    Render Mako templates for Sass files.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    """
    for system in systems:
        if system == "studio":
            system = "cms"
        sh(django_cmd(
            system, settings, 'preprocess_assets',
            '{system}/static/sass/*.scss'.format(system=system),
            '{system}/static/themed_sass'.format(system=system)
        ))
        print("\t\tFinished preprocessing {} assets.".format(system))


def process_xmodule_assets():
    """
    Process XModule static assets.
    """
    sh('xmodule_assets common/static/xmodule')
    print("\t\tFinished processing xmodule assets.")


def restart_django_servers():
    """
    Restart the django server.

    `$ touch` makes the Django file watcher thinks that something has changed, therefore
    it restarts the server.
    """
    sh(cmd(
        "touch", 'lms/urls.py', 'cms/urls.py',
    ))


def collect_assets(systems, settings):
    """
    Collect static assets, including Django pipeline processing.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    """
    for sys in systems:
        sh(django_cmd(sys, settings, "collectstatic --noinput > /dev/null"))
        print("\t\tFinished collecting {} assets.".format(sys))


@task
@cmdopts([('background', 'b', 'Background mode')])
def watch_assets(options):
    """
    Watch for changes to asset files, and regenerate js/css
    """
    # Don't watch assets when performing a dry run
    if tasks.environment.dry_run:
        return

    observer = Observer()

    CoffeeScriptWatcher().register(observer)
    SassWatcher().register(observer)
    XModuleSassWatcher().register(observer)
    XModuleAssetsWatcher().register(observer)

    print("Starting asset watcher...")
    observer.start()
    if not getattr(options, 'background', False):
        # when running as a separate process, the main thread needs to loop
        # in order to allow for shutdown by contrl-c
        try:
            while True:
                observer.join(2)
        except KeyboardInterrupt:
            observer.stop()
        print("\nStopped asset watcher.")


@task
@needs(
    'pavelib.prereqs.install_node_prereqs',
)
@consume_args
def update_assets(args):
    """
    Compile CoffeeScript and Sass, then collect static assets.
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument(
        'system', type=str, nargs='*', default=ALL_SYSTEMS,
        help="lms or studio",
    )
    parser.add_argument(
        '--settings', type=str, default="devstack",
        help="Django settings module",
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Disable Sass compression",
    )
    parser.add_argument(
        '--skip-collect', dest='collect', action='store_false', default=True,
        help="Skip collection of static assets",
    )
    parser.add_argument(
        '--watch', action='store_true', default=False,
        help="Watch files for changes",
    )
    parser.add_argument(
        '--themes_dir', type=str, default=None,
        help="base directory where themes are placed",
    )
    parser.add_argument(
        '--themes', type=str, nargs='*', default=None,
        help="list of themes to compile sass for",
    )
    args = parser.parse_args(args)

    compile_templated_sass(args.system, args.settings)
    process_xmodule_assets()
    compile_coffeescript()

    call_task(
        'pavelib.assets.compile_sass',
        options={'system': args.system, 'debug': args.debug, 'themes_dir': args.themes_dir, 'themes': args.themes},
    )

    if args.collect:
        collect_assets(args.system, args.settings)

    if args.watch:
        call_task('pavelib.assets.watch_assets', options={'background': not args.debug})
