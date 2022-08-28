import re

from bs4 import BeautifulSoup
import requests


requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'


class SigaaAPI(requests.Session):

    def __init__(self, *args, **kwargs):
        super(SigaaAPI, self).__init__(*args, **kwargs)
        self.base_url = 'https://si3.ufc.br/sigaa'
        self.current_soup = None
        self.j_id = None

    def request(self, method, url, *args, **kwargs):
        _url = self.base_url + url

        if self.current_soup:
            j_id = self.current_soup.find('input', id='javax.faces.ViewState')
            if j_id:
                self.j_id = int(re.search(r'(\d+)', j_id['value']).group(1))

        res = super(SigaaAPI, self).request(method, _url, *args, **kwargs)
        self.current_soup = BeautifulSoup(res.content, 'html.parser')

        return res

    def authorize(self, username, password):
        self.get('/verTelaLogin.do')
        return self.post(
            '/logar.do',
            params={'dispatch': 'logOn'},
            data={
                'width': 1920,
                'height': 1080,
                'urlRedirect': '',
                'acao': '',
                'user.login': username,
                'user.senha': password,
                'entrar': 'Entrar'
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.base_url + '/verTelaLogin.do%3bjsessionid=' + self.cookies['JSESSIONID']
            }
        )

    def get_vinculos(self):

        res = self.get('/vinculos.jsf')
        soup = BeautifulSoup(res.content, 'html.parser')
        li_tags = soup.select('section.listagem li')

        vinculos = []
        for i, li in enumerate(li_tags):
            span_tags = li.find_all('span')
            vinculos.append({
                'Index': i + 1,
                'Vinculo': span_tags[2].get_text(),
                'Identificador': span_tags[3].get_text(),
                'Ativo': span_tags[4].get_text() == 'Sim',
                'Outras Informações': span_tags[5].get_text()
            })

        return vinculos

    def set_current_vinculo(self, index=1):

        self.get(
            '/escolhaVinculo.do',
            params={'dispatch': 'escolher', 'vinculo': index}
        )
        self.get('/paginaInicial.do')
        self.get('/verPortalDiscente.do')

    def get_all_cursos(self):

        res = self.get('/graduacao/curriculo/lista.jsf?aba=consultas')
        soup = BeautifulSoup(res.content, 'html.parser')
        select_tag = soup.find('select', id='busca:curso')
        cursos = []
        for curso in select_tag.find_all('option')[1:]:
            cursos.append({
                'id': curso['value'],
                'curso': curso.get_text()
            })

        return cursos

    def get_all_matrizes(self, curso_id):
        self.get('/graduacao/curriculo/lista.jsf?aba=consultas')
        res = self.post(
            '/graduacao/curriculo/lista.jsf',
            data={
                'busca': 'busca',
                'busca:checkCurso': 'on',
                'busca:curso': curso_id,
                'busca:matriz': 0,
                'busca:codigo': '',
                'busca:btnBuscar': 'Buscar',
                'javax.faces.ViewState': f'j_id{self.j_id + 1}'
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self. base_url + '/graduacao/curriculo/lista.jsf?aba=consultas'
            }
        )

        soup = BeautifulSoup(res.content, 'html.parser')
        tr_tags = soup.select('table.listagem > tr')
        matrizes = []
        for tr in tr_tags:
            td_tags = tr.find_all('td')
            a_tag = tr.find('a')
            matriz_id = re.search(
                r',(\d+)\'',
                a_tag['onclick']
            ).group(1)
            matrizes.append({
                'Código': td_tags[0].get_text(),
                'Ano': td_tags[1].get_text(),
                'Matriz': td_tags[2].get_text(),
                'Id': matriz_id
            })

        return matrizes

    def get_grade_curricular(self, matriz_id):

        self.get('/graduacao/curriculo/lista.jsf?')
        res = self.post(
            '/graduacao/curriculo/lista.jsf',
            data={
                'resultado': 'resultado',
                'resultado:relatorio': 'relatorio',
                'id': matriz_id,
                'javax.faces.ViewState': f'j_id{self.j_id + 1}'
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self. base_url + '/graduacao/curriculo/lista.jsf?aba=consultas'
            }
        )

        # soup = BeautifulSoup(open('page.html', 'r').read(), 'html.parser')
        soup = BeautifulSoup(res.content, 'html.parser')
        table_tags = soup.find_all('table', class_='subFormulario')
        disciplinas = []

        for table in table_tags:
            tr_tags = table.select('tr.componentes')
            for tr in tr_tags:
                td_tags = tr.find_all('td')
                disciplinas.append({
                    'Codigo': td_tags[0].get_text(),
                    'Componente': td_tags[1].get_text().replace('\n', '').replace('\t', ''),
                    'CH_Detalhada': td_tags[2].get_text().replace('\n', '').replace('\t', ''),
                    'Tipo': td_tags[3].get_text().replace('\n', '').replace('\t', ''),
                    'Obrigatoria': td_tags[4].get_text() == 'OBRIGATÓRIA',
                    'Pre_Requisitos': [
                        acronym.get_text()
                        for acronym in td_tags[5].find_all('acronym')
                    ],
                    'Equivalencias': [
                        acronym.get_text()
                        for acronym in td_tags[6].find_all('acronym')
                    ]
                })

        return disciplinas
