import discord
from discord.ui import Button, View
import re
#import os

from twitter_video_scraper.twitter_video_scraper import TwitterVideoScraper
from tiktok_video_scraper_web.tiktok_video_scraper_web import TikTokVideoScraperWeb
from tiktok_video_scraper_mobile.tiktok_video_scraper_mobile import TikTokVideoScraperMobile
from instagram_post_scraper.instagram_post_scraper import InstagramPostScraper
from instagram_stories_scraper.instagram_stories_scraper import InstagramStoryScraper
from reddit_video_scraper.reddit_video_scraper import RedditVideoScraper

##################################################################################
# This class is for create buttons dynamically when the post has more than 1 item, 
# each one has a url that must be downloaded and sent to discord
class DynamicView(View):
    
    def __init__(self, video_list: list, site: str):
        super().__init__()

        button_number = 0
        for video in video_list:
            button = Button(label=f"{button_number + 1 }", style=discord.ButtonStyle.primary)
            button.callback = self.create_callback(button, video, site)
            self.add_item(button)
            button_number = button_number + 1

    def create_callback(self, button: Button, video: str, site: str):
        async def callback(interaction: discord.Interaction):
            button.disabled = True
            await interaction.response.edit_message(view=self)
            
            # social can be twitter or instagram, only their carousel is supported
            if site == 'Twitter':
                tw_video = TwitterVideoScraper()
                
                # download video by url, the download do it in the same path
                downloaded_video = tw_video.download([video])

                fixed_video_list = tw_video.ffmpeg_fix(downloaded_video)

                with open(fixed_video_list[0], 'rb') as f:
                    vid = discord.File(f, filename = fixed_video_list[0])
                try:
                    await interaction.followup.send(file=vid)
                except Exception as e:
                    print('video too large')
                    if 'too large' in str(e):
                        await interaction.followup.send(f'el video es demasiado extenso para Discord')

            # social can be twitter or instagram, only their carousel is supported
            if site == 'Instagram':
                ig_story = InstagramStoryScraper()
                
                # download video by url, the download do it in the same path
                downloaded_item_list = ig_story.download([video])

                with open(downloaded_item_list[0], 'rb') as f:
                    vid = discord.File(f, filename = downloaded_item_list[0])
                try:
                    await interaction.followup.send(file=vid)
                except Exception as e:
                    print('video too large')
                    if 'too large' in str(e):
                        await interaction.followup.send(f'el video es demasiado extenso para Discord')

        return callback
################################################################################

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True

client = discord.Client(intents = intents)
messages_author = []


@client.event
async def on_message(message):    

    #if the bot is seeing its own message.
    if message.author == client.user:
        return

    print(message.author.id)
    print(message.content)
    # regex to extract urls from the text given
    extract_url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    try:
        video_url = re.findall(extract_url_regex, message.content)[0][0]
    except Exception as e:
        #await message.channel.send('No se encontro link al video en el mensaje', reference=message)
        #await message.delete()
        return

    site = await check_site(video_url)
    # here start to run the scrapers
    if site:
        # twitter
        if site == 'Twitter':
            video_list, thumbnails, video_nsfw = await run_twitter_video_scraper(video_url)

            # errors handler, (im using video_nsfw like error variable bc its not used in this project)
            if video_nsfw == -1:
                await message.channel.send('hubo un error, si persiste contacta al admin', reference=message)
                return
            if video_nsfw == -2:
                await message.channel.send(f'videos nsfw no estan soportados en Discord', reference=message)
                return
            if video_nsfw == -3:
                await message.channel.send('el archivo es demasiado extenso para discord', reference=message)
                return

            # send the video/image to discord
            # 1 video
            if len(video_list) == 1:
                send_video_result = await send_video_to_discord(video_list, message)            
                if send_video_result == True:
                    print('x/twitter videos sent successfully')
            # +1 video
            else:
                view = DynamicView(video_list, site)
                await message.channel.send(f"Hay {len(video_list)} videos/images:", view=view, reference=message)
            return
        # tiktok
        if site == 'TikTok':
            video_list, video_thumbnails, video_nsfw = await run_tiktok_video_scraper(video_url)

            # errors handler
            if video_nsfw == -1:
                await message.channel.send('hubo un error, si persiste contacta al admin', reference=message)
                return

            # send the video/image to discord
            send_video_result = await send_video_to_discord(video_list, message)            
            if send_video_result == True:
                print('tiktok videos sent successfully')
            return

        # reddit
        if site == 'Reddit':
            video_list, video_thumbnails, video_nsfw = await run_reddit_video_scraper(video_url)

            # errors handler
            if video_nsfw == 1:
                await message.channel.send('videos nsfw no estan soportados en Discord', reference=message)
                return
            if video_nsfw == -1:
                await message.channel.send('hubo un error, si persiste contacta al admin', reference=message)
                return

            # send the video/image to discord
            send_video_result = await send_video_to_discord(video_list, message)            
            if send_video_result == True:
                print('reddit videos sent successfully')
            return

        if site == 'Instagram':
            video_list, video_thumbnails, video_nsfw = await run_instagram_video_scraper(video_url)

            # send the video/image to discord
            # 1 video
            if len(video_list) == 1:
                send_video_result = await send_video_to_discord(video_list, message)            
                if send_video_result == True:
                    print('instagram videos sent successfully')
            # +1 video
            else:
                view = DynamicView(video_list, site)
                await message.channel.send(f"Hay {len(video_list)} videos/images:", view=view, reference=message)
            return


    return

#--------------------------------------------------------------------------------
async def check_site(url: str) -> tuple[str, bool]:
    """ check what type of url was entered and classify it, 
        if the social is not supported it returns false """

    #instagram
    if 'instagram.com' in url:
        return 'Instagram' 
    #twitter
    if 'twitter.com' in url or 'x.com' in url:
        return 'Twitter'
    #tiktok
    if 'tiktok.com' in url:
        return 'TikTok'
    #reddit
    if 'reddit.com' in url:
        return 'Reddit'
    
    return False
#--------------------------------------------------------------------------------
async def run_twitter_video_scraper(video_url: str) -> tuple:
    # this funcion can return:
    #
    #   return fixed_video_list, video_thumbnails, False
    #   1 video: fixed_video_list, all ready downloades and fixed videos list
    #            video_thumbnails, thumb of the video/s
    #            nsfw, not supported

    # return video_url_list, video_thumbnails, False 
    #   +1 video:video_url_list, x/twitter direct video link list
    #            video_thumbnails, thumb of the video/s
    #            nsfw, not supported

    # create scraper video object
    tw_video = TwitterVideoScraper()

    # set the proxy (optional, u can run it with ur own ip)
    #tw_video.set_proxies('<your http proxy>', '<your https proxy')

    try:
        # get post id from url, this method recive the video url to scrap
        restid = tw_video.get_restid_from_tw_url(video_url)

        # get guest token, set it in cookies
        tw_video.get_guest_token()

        # get video url and thumbnails from video id
        video_url_list, video_thumbnails, video_nsfw = tw_video.get_video_url_by_id_graphql(restid)
        #video_url_list = tw_video.get_video_url_by_id_syndication(restid)

        # if its nsfw content close session and return error -2
        if video_nsfw == True:
            tw_video.tw_session.close()
            return [],[],-2
        else:
            # it 1 video
            if len(video_url_list) == 1:
                # download video by url
                downloaded_video_list = tw_video.download(video_url_list)

                if downloaded_video_list:
                    # fix video to make it shareable (optional, but e.g android reject the default format)
                    # remember install ffmpeg to use this method
                    fixed_video_list = tw_video.ffmpeg_fix(downloaded_video_list)

                    tw_video.tw_session.close()

                    return fixed_video_list, video_thumbnails, False
                else:
                    return [],[],-1
            # +1 videos
            else:
                return video_url_list, video_thumbnails, False         

    # something went wrong, check the exception
    except SystemExit as e:
        print('exception:', e)
        return [],[], -1
#--------------------------------------------------------------------------------
async def run_tiktok_video_scraper(tiktok_url: str) -> tuple:

    # create scraper video object
    tiktok_video = TikTokVideoScraperWeb()

    # set the proxy (optional, u can run it with ur own ip)
    #tiktok_video.set_proxies('socks5://157.230.250.185:2144', 'socks5://157.230.250.185:2144')

    try:
        # get video id from url
        video_id = tiktok_video.get_video_id_by_url(tiktok_url)
        
        # get video url from video id
        tiktok_video_url, video_thumbnail = tiktok_video.get_video_data_by_video_url(tiktok_url)

        # download video by url
        downloaded_video_list = tiktok_video.download(tiktok_video_url, video_id)

    # something went wrong, trying TikTokVideoScraperMobile
    except SystemExit as e:

        # create scraper video object
        tiktok_video = TikTokVideoScraperMobile()

        # set the proxy (optional, u can run it with ur own ip)
        #tiktok_video.set_proxies('socks5://157.230.250.185:2144', 'socks5://157.230.250.185:2144')

        try:
            # get video id from url
            video_id = tiktok_video.get_video_id_by_url(tiktok_url)
            
            # get video url from video id
            tiktok_video_url, video_thumbnail = tiktok_video.get_video_data_by_video_id(video_id)

            # download video by url
            downloaded_video_list = tiktok_video.download(tiktok_video_url, video_id)
        
        # something went wrong, check the exception
        except SystemExit as e:
            print('exception:', e)
            return [],[], -1

    tiktok_video.tiktok_session.close()

    return downloaded_video_list, video_thumbnail, False

#--------------------------------------------------------------------------------
async def run_reddit_video_scraper(reddit_url: str) -> tuple:
    try:
        # create scraper video object
        reddit_video = RedditVideoScraper()

        # set the proxy (optional, u can run it with ur own ip)
        #reddit_video.set_proxies('<your http proxy>', '<your https proxy')

        # get video info from url
        reddit_video_info = reddit_video.get_video_json_by_url(reddit_url)

        # get the video details
        reddit_video_urls, video_thumbnail, video_nsfw = reddit_video.reddit_video_details(reddit_video_info)

        # download the video and audio
        download_details = reddit_video.download(reddit_video_urls)

        # join the video and audio
        # remember install ffmpeg if u dont have it
        downloaded_video_list = reddit_video.ffmpeg_mux(download_details)
        # something went wrong, check the exception
        reddit_video.reddit_session.close()

        return downloaded_video_list, video_thumbnail, video_nsfw
    except SystemExit as e:
        print('exception:', e)
        return [],[], -1
    
#--------------------------------------------------------------------------------
async def run_instagram_video_scraper(ig_url: str) -> tuple:
    if '/stories/' in ig_url or '/s/' in ig_url:
        return await run_instagram_stories_scraper(ig_url)

    if '/p/' in ig_url or '/reel/' in ig_url or '/tv/' in ig_url:
        return await run_instagram_post_scraper(ig_url)
#--------------------------------------------------------------------------------
async def run_instagram_stories_scraper(ig_url: str) -> tuple:
    # set your ig username and password
    your_username = 'your instagram username'
    your_password = 'your instagram password'

    cookies_path = 'ig_cookies'

 
    # create scraper stories object    
    ig_story = InstagramStoryScraper()

    # set the proxy (optional, u can run it with ur own ip)
    ig_story.set_proxies('', '')

    try:
    # get the username and story id by url
        username, story_id = ig_story.get_username_storyid(ig_url)

        # get the user id or highlights id
        user_id = ig_story.get_userid_by_username(username, story_id)

        # perform login or load cookies
        ig_story.ig_login(your_username, your_password, cookies_path)

        # get the stories urls (sequential with get_story_filesize)
        stories_urls, thumbnail_urls = ig_story.get_ig_stories_urls(user_id)

        # get the video filesize (sequential with get_ig_stories_urls)
        #storysize = ig_story.get_story_filesize(stories_urls)
        #[print('filesize: ~' + filesize + ' bytes') for filesize in storysize]
    except SystemExit as e:
        print('exception:', e)
        return [],[], -1

    if len(stories_urls) == 1:
        # download the stories
        downloaded_item_list = ig_story.download(stories_urls)

        ig_story.ig_session.close()

        # * thumbnail_urls are the direct link to instagram. 
        # you will probably have to download them too, due to cors problems with Instagram
        return downloaded_item_list, thumbnail_urls, False
    
    else:
        ig_story.ig_session.close()

        # idem thubnails *
        return stories_urls, thumbnail_urls, False
#--------------------------------------------------------------------------------
async def run_instagram_post_scraper(ig_post_url: str) -> tuple:
    # create scraper post object    
    ig_post = InstagramPostScraper()

    # set the proxy (optional, u can run it with ur own ip)
    #ig_post.set_proxies('<your http/socket4/socket5 proxy>', '<your https proxy')

    try:
        # get video id from url    
        post_id = ig_post.get_post_id_by_url(ig_post_url)

        # get csrf token
        csrf_token = ig_post.get_csrf_token(post_id)

        # get post urls from video id
        ig_post_urls, thumbnail_urls = ig_post.get_ig_post_urls(csrf_token, post_id)

    except SystemExit as e:
        print('exception:', e)
        return [],[], -1
    
    if len(ig_post_urls) == 1:
        # download post items
        downloaded_item_list = ig_post.download(ig_post_urls, post_id)
        
        ig_post.ig_session.close()

        # * thumbnail_urls are the direct link to instagram. 
        # you will probably have to download them too, due to cors problems with Instagram
        return downloaded_item_list, thumbnail_urls, False
    else:
        ig_post.ig_session.close()

        # idem thubnails *
        return ig_post_urls, thumbnail_urls, False
#--------------------------------------------------------------------------------
async def send_video_to_discord(video_list, message):
    """ send the video or img to discord, 
        and then deletes the sent file from disk """

    for video_name in video_list:
        try:
            with open(video_name, 'rb') as video_or_pic:
                # in this case delete the video from your disk, but you can keep it
                #os.system(f'rm {video_name}') 
                vid = discord.File(video_or_pic, filename = video_name)
        except Exception as e:
            return False
        
        try:
            await message.channel.send(file=vid, reference=message)
        except Exception as e:
            if 'too large' in str(e):
                print('video too large')
                await message.channel.send(f'el video es demasiado extenso para Discord', reference=message)
            return False
            
    return True
#--------------------------------------------------------------------------------

client.run('your bot token')
