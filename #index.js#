//var request = require('request');
var _ = require('underscore');
var fs = require('fs');
var exec = require('child_process').exec;
_.mixin( require('underscore.deferred') );
//var inflection = require('inflection');
var Twit = require('twit');
var T = new Twit(require('./config.js'));
var wordfilter = require('wordfilter');
var ent = require('ent');

var WIDTH = 800,
    HEIGHT = 400;
 
var Canvas = require('canvas'),
    Image = Canvas.Image,
    canvas = new Canvas(WIDTH, HEIGHT),
    ctx = canvas.getContext('2d');


var authors = [ { 'name': 'Abraham Lincoln',
                  'images': ['lincoln1.jpg']
                },
                { 'name': 'Albert Einstein',
                  'images': ['einstein1.jpg']
                },
                { 'name': 'Mark Twain',
                  'images': ['twain.jpg']
                },
                { 'name': 'Winston Churchill',
                  'images': ['churchill.jpg']
                }
             ];

var imgdir = __dirname + '/out.png';
    
var fonts = ['Chalkboard', 'Herculanum', 'Noteworthy Light', 'Papyrus'];
var bgs = ['bg1.jpg', 'bg2.jpg', 'bg3.jpg', 'bg4.jpg'];

var terms = ['bravery', 'innovation', 'courage', 'excellence', 'achieve'];

wordfilter.addWords(['-']); // Try to exclude attributions

function choice(list) {
    return list[_.random(0, list.length - 1)];
}

function wrapText(context, text, x, y, maxWidth, lineHeight) {
    var words = text.split(' ');
    var line = '';
    
    for(var n = 0; n < words.length; n++) {
        var testLine = line + words[n] + ' ';
        var metrics = context.measureText(testLine);
        var testWidth = metrics.width;
        if (testWidth > maxWidth && n > 0) {
            context.fillText(line, x, y);
            line = words[n] + ' ';
            y += lineHeight;
        }
        else {
            line = testLine;
        }
    }
    context.fillText(line, x, y);
}

Array.prototype.pick = function() {
  return this[Math.floor(Math.random()*this.length)];
};

Array.prototype.pickRemove = function() {
  var index = Math.floor(Math.random()*this.length);
  return this.splice(index,1)[0];
};

function generate() {
    var dfd = new _.Deferred();
    search(choice(terms)).then(function (p) {
        dfd.resolve(p); 
    });
    return dfd.promise();
}
var ascii = /^[\x00-\x7F]*$/;

function replaceAll(find, replace, str) {
  return str.replace(new RegExp(find, 'g'), replace);
}

function tweet() {
    var maxwidth = 450,
        x = 25,
        y = 60,
        lineHeight = 32,
        result,
        img,
        author = choice(authors),
        portrait = choice(author['images']),
        bg = choice(bgs),
        font = choice(fonts),
        mt;

    generate().then(function(results) {

        results = _.filter(results, function (tweet) {
            if (ascii.test(tweet) && !/#/.test(tweet) && !/-|~/.test(tweet)) {
                return tweet;
            }            
        });
        result = choice(results);
        result = replaceAll('\n', '', result);
        
        if (!wordfilter.blacklisted(result)) {
            console.log(result);
            ctx.fillStyle = '#fff';
            ctx.fillRect(0, 0, WIDTH, HEIGHT);
            fs.readFile(__dirname + '/images/' + bg, function(err, data) {
                if (err) { throw err; }
                img = new Image(); // Create a new Image
                img.src = data;
                ctx.drawImage(img, 0, 0, WIDTH, HEIGHT);

                ctx.font = '30px ' + font;
                ctx.fillStyle = 'black';
                mt = ctx.measureText(result);
                wrapText(ctx, result, x, y, maxwidth, lineHeight);                
                ctx.font = '30px Zapfino';
                ctx.fillText('- ' + author.name, x, HEIGHT - lineHeight);
                

                fs.readFile(__dirname + '/images/' + portrait, function(err, data) {
                    if (err) { throw err; }
                    img = new Image(); // Create a new Image
                    img.src = data;
                    ctx.drawImage(img, WIDTH - img.width, y, img.width / 1.2, img.height / 1.2);
                    
                    makePng(canvas).done(function() {
                        var b64content = fs.readFileSync(imgdir, { encoding: 'base64' });

                        // first we must post the media to Twitter
                        T.post('media/upload', { media: b64content }, function (err, data, response) {
                            if (err) { console.log(err); throw err; }                            
                            // now we can reference the media and post a tweet (media will attach to the tweet)
                            var mediaIdStr = data.media_id_string;
                            var params = { status: '', media_ids: [mediaIdStr] };
                            
                            T.post('statuses/update', params, function (err, data, response) {

                            });
                        });

                    });
                });
            });
        }
  });
}

function search(term) {
    console.log('searching',term);
    var dfd = new _.Deferred();
    T.get('search/tweets', { q: term, count: 100, lang: 'en' }, function(err, reply) {
        //console.log('search error:',err);
        var tweets = reply.statuses;
        tweets = _.chain(tweets)
        // decode weird characters
            .map(function(el) {
                if (el.retweeted_status) {
                    return ent.decode(el.retweeted_status.text);
                }
                else {
                    return ent.decode(el.text);
                }
            })
            .reject(function(el) {
                // throw out quotes and links and replies
                return el.indexOf('http') > -1 || el.indexOf('@') > -1 || el.indexOf('"') > -1;
            })
            .uniq()
            .value();
//        console.log(tweets);
        dfd.resolve(tweets);
  });
  return dfd.promise();
}

function makePng(canvas) {
    console.log('making canvas');
    var dfd = new _.Deferred();
    var fs = require('fs'),
        out = fs.createWriteStream(imgdir),
        stream = canvas.pngStream();
    
    stream.on('data', function(chunk){
        out.write(chunk);
    });
    
    stream.on('end', function(){
        console.log('saved png');
        exec('convert out.png out.png').on('close', function() {
            dfd.resolve('done!');
        });
    });
  return dfd.promise();
}

// Tweet every 60 minutes
/*
@setInterval(function () {
  try {
    tweet();
  }
  catch (e) {
    console.log(e);
  }
}, 1000 * 60 * 60);
    */
    
// Tweet once on initialization
tweet();
 
