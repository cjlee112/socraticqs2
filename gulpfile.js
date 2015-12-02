var gulp = require('gulp'),
    stylus = require('gulp-stylus'), 
    csso = require('gulp-csso'), 
    uglify = require('gulp-uglify'), 
    concat = require('gulp-concat'),
    minifyCSS = require('gulp-minify-css'),
    autoprefixer = require('gulp-autoprefixer');

gulp.task('default', function() {
    gulp.run("js");
    gulp.run("css")

});
//  JS
gulp.task('js', function() {
    gulp.src(['./mysite/mysite/static/js/*.js', ])
        .pipe(concat('main..min.js')) 
        .pipe(gulp.dest('./public/js'))
        .pipe(uglify());
});
// CSS
gulp.task('css', function() {
    gulp.src(['./mysite/mysite/static/css/*.css', ])
        .pipe(minifyCSS())
        .pipe(autoprefixer('last 2 version', 'safari 5', 'ie 8', 'ie 9'))
        .pipe(concat('main.css')) 
        .pipe(gulp.dest('./public/css'));
});
