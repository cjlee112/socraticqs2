function Logging(){
  var stream = through.obj(function (file, enc, callback) {
    console.log("stream:");
    console.log(file, enc, callback);
    this.push(file);
    return callback();
  });

  return stream;
}

var gulp = require('gulp'),
    stylus = require('gulp-stylus'), 
    csso = require('gulp-csso'), 
    uglify = require('gulp-uglify'), 
    concat = require('gulp-concat'),
    minifyCSS = require('gulp-minify-css'),
    autoprefixer = require('gulp-autoprefixer');
var through = require('through2');



//  JS
gulp.task('js', function() {
   return gulp.src(['./mysite/assets/js/src/*.js', ])
       .pipe(concat('main.min.js'))
       .pipe(uglify())
       .on('error', console.log)
       .pipe(gulp.dest('./mysite/mysite/static/js/'));

});

// CSS
gulp.task('css', function() {
    return gulp.src(['./mysite/assets/css/src/*.css', ])
        .pipe(minifyCSS())
        .pipe(autoprefixer('last 2 version', 'safari 5', 'ie 8', 'ie 9'))
        .pipe(concat('main.css'))
        .pipe(gulp.dest('./mysite/mysite/static/css/'));
});

gulp.task('default', ['js', 'css']);