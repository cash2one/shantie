#! /usr/bin/env python
# -*- coding: utf-8 -*-
#Author:pako
#Email:zealzpc@gmail.com
"""
some db interface 
"""
from config import *
import datetime
con = mdb.con
import logging

######################db.init######################
gfw = GFW()
gfw.set(open(os.path.join('keyword.txt')).read().split('\n'))

def update_post(url,db,content=None,is_open=1):
    if is_open ==0 :
        con[db].post.update({'url':url},{'$set':{'is_open':is_open,'find_time':time.time(),'last_click_time':time.time()}})
    else:
        con[db].post.update({'url':url},{'$set':{'is_open':is_open,'find_time':time.time(),'last_click_time':time.time()}})
        
"""
def kds_review():
    db = con['kds']
    yesterdat=time.time()-48*3600
    #yesterdat=time.time()-100
    old_post=db.post.find({'create_time':{'$lt':yesterdat},'is_open':1})
    #old_post=db.post.find({'is_open':1})
    #old_post=post.find({'is_open':1})
    logging.info('old post amount:%s'%old_post.count())
    root="http://club.pchome.net/" #root = "http://tieba.baidu.com/p/" try:
    try:
        for tiezi in old_post:
                post_url=str(os.path.join(root,str(tiezi['url'])))  
                post_html=get_html(post_url)
                if post_html is None:
                    continue
                #post_soup = BeautifulSoup(post_content_all,fromEncoding='gbk')
                #post_content=post_soup.find('div',{'class':'mc'})
                if 'backHome' in post_html:
                    logging.error( u'>>>>>>>>>>>>>>>>发现了一个被删除的帖子(%s)!<<<<<<<<<<<<<<<<<<<<'%post_url)
                    update_post(url = tiezi['url'],db='kds',is_open=0)   
                else:
                    logging.info('>>>>>>>>>>>>>>>>删除了已经存在了48h的帖子%s !<<<<<<<<<<<<<<<<<<<<'%tiezi['url'])
                    db.post.remove({'url':tiezi['url']}) 
    except Exception,e:
        traceback.print_exc() 
        pass
"""

def save_post_img(post_id):
    """
    保存帖子的图片去七牛
    """
    content = []
    post_cover_img = ''
    post_info = mdb.baidu.post.find_one({'url':post_id})
    need_reset = False
    if post_info:
        for r in post_info['content']:
            reply_content = []
            for e in r['reply_content']:
                if e['tag'] == 'img':
                    img_key = '%s_%s'%(str(post_info['_id']),tools.random_key(1,24))
                    #tools.update_web_file(e['content']+'?kilobug',img_key)
                    tools.update_web_file(e['content'],img_key)
                    e['old_content'] = e['content']
                    e['content'] = img_key
                    need_reset = True
                    if not post_cover_img:
                        post_cover_img = img_key
                reply_content.append(e)
            content.append(r)
        if need_reset:
            logging.warning('>>>>>>>>>>>>>reset baidu post %s content '%post_info['url'])
            mdb.baidu.post.update({'_id':post_info['_id']},{'$set':{'content':content,'post_cover_img':post_cover_img}})



def tieba_review(dbname):
    db = con[dbname]
    yesterdat=time.time()-24*3600
    #yesterdat=time.time()-100
    if server_name.name == 'online':
        old_post=db.post.find({'create_time':{'$lt':yesterdat},'is_open':1,'tieba_name':'liyi'})
    else:
        old_post=con[dbname].post.find({'is_open':1})

    logging.info('old post amount:%s'%old_post.count())
    root = "http://tieba.baidu.com/p/"
    #try:
    for tiezi in old_post:
            post_url=os.path.join(root,str(tiezi['url']))  
            post_content_all=tools.get_html(post_url)
            cover_img = tiezi.get('post_cover_img','')
            logging.info("cover img:%s"%cover_img)
            if not post_content_all or len(tiezi['content']) < 5:
                logging.warning("帖子下载失败!")
                db.post.remove({'url':tiezi['url']}) 
                continue

            if 'error_404_iframe' in post_content_all :
            #TODO
            #if True:
                cover_img_info = tools.update_web_file(cover_img,str(tiezi['_id']),settings.get('photo_test_bucket'))
                logging.info('cover_img_info:%s'%cover_img_info)
                if cover_img_info.get("hash",''):
                    #判断是否有重复的封面
                    hash_exist = mdb.baidu.post.find_one({"cover_hash":cover_img_info['hash']})
                    if hash_exist:
                        mdb.baidu.post.remove({"cover_hash":cover_img_info["hash"]})
                        continue

                if cover_img_info.get('fsize',0) < 20480:
                    logging.warning("帖子封面图太小!")
                    db.post.remove({'url':tiezi['url']}) 
                    continue
                else:
                    mdb.baidu.post.update({'_id':tiezi['_id']},{'$set':{'cover_hash':cover_img_info['hash']}})
                org_title= tiezi['title'].encode('utf-8')
                filter_title = gfw.replace(org_title)
                print type(filter_title),len(filter_title)
                print type(tiezi['title']),len(tiezi['title'])
                logging.warning(u'filter_title:%s'%filter_title.decode('utf-8'))
                logging.warning(u'title:%s'%tiezi['title'])
                if filter_title.decode('utf-8') != tiezi['title']:
                    logging.warning( u'>>>>>>>>>>>>>>>>发现了一个被删除的帖子(%s)! 现在删除<<<<<<<<<<<<<<<<<<<<'%post_url)
                    db.post.remove({'url':tiezi['url']}) 
                else:
                    logging.error( u'>>>>>>>>>>>>>>>>发现了一个被删除的帖子(%s)!<<<<<<<<<<<<<<<<<<<<'%post_url)
                    save_post_img(tiezi['url'])
                    update_post(url = tiezi['url'],db=dbname,is_open=0)   
            else:
                logging.info('>>>>>>>>>>>>>>>>删除了已经存在了24h的帖子%s !<<<<<<<<<<<<<<<<<<<<'%tiezi['url'])
                db.post.remove({'url':tiezi['url']}) 
                    
    #except Exception,e:
    #    traceback.print_exc() 
    #    pass


if __name__ == "__main__":
    mdb.init()
    while True:
        try:
            tieba_review('baidu')
            time.sleep(600)
        except Exception,e:
            print('\n'*9)
            traceback.print_exc()
            print('\n'*9)
