'use strict';

var gulp = require('gulp');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var sass = require('gulp-sass');
var maps = require('gulp-sourcemaps');
var handlebars = require('gulp-handlebars');
var wrap = require('gulp-wrap');
var declare = require('gulp-declare');
var del = require('del');
var runSequence = require('run-sequence');
var imagemin = require('gulp-imagemin');
var useref = require('gulp-useref');
var cleanCSS = require('gulp-clean-css');
var gulpif = require('gulp-if');
var jsdoc = require('gulp-jsdoc3');
var insert = require('gulp-insert');
var jshint = require('gulp-jshint');
var replace = require('gulp-replace');

// Compile handlebars templates
// http://handlebarsjs.com/precompilation.html
// https://www.npmjs.com/package/gulp-handlebars
gulp.task('precompile-templates', function(){
  return gulp.src('src/js/views/*.hbs')
    .pipe(handlebars({
      handlebars: require('handlebars')
    }))
    .pipe(wrap('Handlebars.template(<%= contents %>)'))
    .pipe(declare({
      namespace: 'CUI.views',
      noRedeclare: true // Avoid duplicate declarations
    }))
    .pipe(concat('compiled.templates.js'))
    .pipe(insert.prepend('/** @file Creates the CUI.templates namespace and defines all templates. */ \n var CUI = CUI || {}; \n /** Contains Handlebars view templates \n * @namespace */ \n CUI.views = CUI.views || {}; \n'))
    .pipe(gulp.dest('src/js/views'));
});

// Compile sass
gulp.task('compile-sass', function(){
  return gulp.src('src/sass/app.scss')
    .pipe(maps.init())
    .pipe(sass())
    .pipe(maps.write('./'))
    .pipe(gulp.dest('src/css'));
});

// Optimize images
gulp.task('optimize-images', function(){
  return gulp.src('src/img/**/*.+(png|jpg|gif|svg)')
    .pipe(imagemin())
    .pipe(gulp.dest('dist/img'));
});

// Concat, optimize, and inject js and css into html
// https://www.npmjs.com/package/gulp-useref
gulp.task('inject-assets', function(){
  return gulp.src('src/*.html')
    .pipe(useref())
    .pipe(gulpif('*.js', uglify()))
    .pipe(gulpif('*.css', cleanCSS({compatibility: 'ie8'})))
    .pipe(gulp.dest('dist'));
});

// Document task
gulp.task('doc', function(){
  // 'README.md',
  return gulp.src(['src/js/**/*.js'], {read: false})
    .pipe(jsdoc());
});

// Lint task
gulp.task('lint', function(){
  return gulp.src(['src/js/**/*.js', '!src/js/views/compiled.templates.js', '!src/js/plugins/jquery-1.9.1-for-ie8.min.js'])
    .pipe(jshint())
    .pipe(jshint.reporter('default'));
});

// Clean task
gulp.task('clean', function(){
  return del(['dist', 'docs']);
});

// Watch task
gulp.task('watch', function(){
  gulp.watch('src/sass/**/*.scss', ['compile-sass']);
  gulp.watch('src/js/**/*.hbs', ['precompile-templates']);
  gulp.watch('src/js/**/*.js', ['lint']);
})

// Build task
gulp.task('build', function(callback){
  runSequence('clean', 'lint', ['precompile-templates', 'compile-sass', 'optimize-images', 'doc'], 'inject-assets', callback);
});

// Default task
gulp.task('default', function(){
  gulp.start('build');
});
