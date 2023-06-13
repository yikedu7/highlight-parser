import requests
from bs4 import BeautifulSoup
import urllib.parse
import fire


class ParserWrapper(object):

    def __init__(self, link, format=None, context_range=300):
        self.link = link
        self.format = format
        self.context_range = context_range

    def parse(self):
        response = requests.get(self.link)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string
        page_url = response.url.split('#')[0]
        highlight_url = response.url
        page_text = soup.get_text(separator="\n")

        anchor = parse_anchor(self.link)
        begin, end = locate_by_anchor(page_text, anchor)
        highlight = page_text[begin:end]
        if anchor['text'] is None:
            context = highlight
        else:
            context_begin, context_end = begin, end
            while context_begin > 0 \
                    and begin - context_begin <= self.context_range \
                    and page_text[context_begin] != '\n':
                context_begin -= 1
            while context_end < len(page_text) \
                    and context_end - end <= self.context_range \
                    and page_text[context_end] != '\n':
                context_end += 1
            context = page_text[context_begin:context_end].strip()

        result = {'title': title, 'page_url': page_url, 'highlight_url': highlight_url, 'highlight': highlight,
                  'context': context}
        if self.format:
            result = format_highlight_info(result, self.format)
        return result


def parse_anchor(link) -> dict:
    begin, end, text = None, None, None

    anchor_text = link.split('#:~:text=')[-1].split(',')
    anchor_text = [urllib.parse.unquote(text) for text in anchor_text]
    if len(anchor_text) == 1:
        # Case1: https://www.coindesk.com/business/2022/01/17/mechanism-capital-launches-100m-play-to-earn-gaming-fund/#:~:text=on%20decentralized%20finance
        text = anchor_text[0]
    elif len(anchor_text) == 2:
        # Case2: https://www.coindesk.com/business/2022/01/17/mechanism-capital-launches-100m-play-to-earn-gaming-fund/#:~:text=Originally%20founded%20with,press%20release%20Monday.
        begin, end = anchor_text
    elif len(anchor_text) == 3:
        # Case3: https://www.coindesk.com/business/2022/01/17/mechanism-capital-launches-100m-play-to-earn-gaming-fund/#:~:text=a%20focus%20on-,decentralized,-finance%20(DeFi)%20in
        begin, text, end = anchor_text
    return {'begin': begin, 'end': end, 'text': text}


def locate_by_anchor(page_text, anchor) -> tuple:
    if anchor['begin'] and anchor['end']:
        begin, end = anchor['begin'], anchor['end']
        begin_index = page_text.find(begin)
        end_index = page_text.find(end)
        if anchor['text']:
            text = anchor['text']
            text_index = page_text.find(sub=text, start=begin_index + len(begin), end=end_index)
            return text_index, text_index + len(text)
        else:
            return begin_index, end_index + len(end)
    elif anchor['text']:
        text = anchor['text']
        text_index = page_text.find(text)
        return text_index, text_index + len(text)


def format_highlight_info(highlight_info, format):
    if format == 'markdown':
        highlight = f"[**{highlight_info['highlight']}**]({highlight_info['highlight_url']})"
        context = highlight_info['context'].replace(highlight_info['highlight'], highlight)
        return f"[{highlight_info['title']}]({highlight_info['page_url']})\n\n" \
               f"{context}\n"
    elif format == 'html':
        highlight = f"<a href='{highlight_info['highlight_url']}'><b>{highlight_info['highlight']}</b></a>"
        context = highlight_info['context'].replace(highlight_info['highlight'], highlight)
        return f"<a href='{highlight_info['page_url']}'>{highlight_info['title']}</a><br/><br/>" \
               f"{context}<br/>"


def main():
    fire.Fire(ParserWrapper, name='hlp')


if __name__ == '__main__':
    main()
