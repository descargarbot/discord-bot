# discord bot (descargarbot)
A Discord Bot to download videos and images from socials. Send the link of the video/image and the bot will respond with the video/image.
<br>
<h2>dependencies</h2>
<code>Python 3.9+</code>
<code>discord.py</code>
<code>asyncio</code>
<br>
<br>
<h2>install dependencies</h2>
<ul>
<li><h3>discord.py</h3></li>
  <code>pip install discord.py</code>
  <br>
<li><h3>asyncio</h3></li>
  <code>pip install asyncio</code>
  <br>
<li><h3>classes to download</h3></li>
  you need to clone the classes to download (and their dependencies).<br>
  in the bot you can see this like:
  <br><br>
  
    from twitter_video_scraper import TwitterVideoScraper
    from tiktok_video_scraper_web import TikTokVideoScraperWeb
    from tiktok_video_scraper_mobile_v2 import TikTokVideoScraperMobile
    from instagram_post_scraper import InstagramPostScraper
    from instagram_stories_scraper import InstagramStoryScraper
    from reddit_video_scraper import RedditVideoScraper
  
  <ul>
  <li> <a href="https://github.com/descargarbot/twitter-video-scraper" > x / twitter</a> </li>
  <li> <a href="https://github.com/descargarbot/tiktok-video-scraper-web" > tiktok web</a> </li>
  <li> <a href="https://github.com/descargarbot/tiktok-video-scraper-mobile" > tiktok mobile</a> </li>
  <li> <a href="https://github.com/descargarbot/instagram-post-scraper" > instagram posts</a> </li>
  <li> <a href="https://github.com/descargarbot/instagram-story-scraper" > instagram stories</a> </li>
  <li> <a href="https://github.com/descargarbot/reddit-video-scraper" > reddit</a> </li>
  </ul>
<br>
</ul>
<h2>get your bot token</h2>
  Go to Discord and create a bot with all intents and admin permissions, use the token provided in the line 452<br><br>
  
    client.run('your bot token')
  <br>
  And just run the bot with python<br><br>
  
    python3 discord_bot.py
<br>
<h2>online</h2>
<ul>
  ⤵
  <li> <a href="https://discord.gg/gcFVruyjeQ" > Discord Bot 🤖 </a></li>
</ul>
<br>

