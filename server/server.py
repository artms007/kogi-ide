import sys
import os
import logging
import re
import modules

from pyls_jsonrpc.dispatchers import MethodDispatcher
from pyls_jsonrpc.endpoint import Endpoint
from pyls_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

IS_KANJI = re.compile(r'[一-龥]+')
IS_ZENKAKU = re.compile(r'[ぁ-んァ-ンー-龥]+')

# logのファイル
logging.basicConfig(
  handlers = [
    logging.FileHandler(
      filename = f"{os.path.expanduser('~/Desktop')}/lse-in-python.log",
      encoding='utf-8',
      mode='a+'
    )
  ],
  level = logging.DEBUG,
  format = "%(relativeCreated)08d[ms] - %(name)s - %(levelname)s - %(processName)-10s - %(threadName)s -\n*** %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
log = logging.getLogger("pyls_jsonrpc")
log.addHandler(console)


class SampleLanguageServer(MethodDispatcher):
  def __init__(self):
    self.jsonrpc_stream_reader = JsonRpcStreamReader(sys.stdin.buffer)
    self.jsonrpc_stream_writer = JsonRpcStreamWriter(sys.stdout.buffer)
    self.endpoint = Endpoint(self, self.jsonrpc_stream_writer.write)
    self.lastDocument = ''

  def start(self):
    self.jsonrpc_stream_reader.listen(self.endpoint.consume)

  # クライアントからサーバに 'method': 'initialize' が渡った時に実行されるメソッド
  def m_initialize(self, rootUri=None, **kwargs):
    # ここの設定でどのタイミングで通信するか等を決めるっぽい
    return {"capabilities": {
      'codeActionProvider': True,
      # 'codeLensProvider': {
      #   'resolveProvider': False,  # We may need to make this configurable
      # },
      # 'completionProvider': {
      #   'resolveProvider': False,  # We know everything ahead of time
      #   'triggerCharacters': ['.']
      # },
      'documentFormattingProvider': True,
      # 'documentHighlightProvider': True,
      # 'documentRangeFormattingProvider': True,
      # 'documentSymbolProvider': True,
      # 'definitionProvider': True,
      # 'hoverProvider': True,
      # 'referencesProvider': True,
      # 'renameProvider': True,
      # 'foldingRangeProvider': True,
      # 'signatureHelpProvider': {
      #   'triggerCharacters': ['(', ',', '=']
      # },
      'textDocumentSync': {
        # 0 : NONE
        # 1 : FULL
        # 2 : INCREMENTAL
        'change': 1,
        'save': {
          'includeText': True,
        },
        'openClose': True,
      },
      'workspace': {
        'workspaceFolders': {
          'supported': True,
          'changeNotifications': True
        }
      }
    }}

  # クライアントからサーバに 'method': 'textDocument/didClose' が渡った時に実行されるメソッド
  def m_text_document__did_close(self, textDocument=None, **_kwargs):
    pass

  # クライアントからサーバに 'method': 'textDocument/didOpen' が渡った時に実行されるメソッド
  # 適当に0行0文字目から5行5文字目までの文字をWARNING扱い（指定範囲が存在しなくてもエラーにはならない）
  def m_text_document__did_open(self, textDocument=None, **_kwargs):
    self.lastDocument = textDocument['text']
    self.endpoint.notify("textDocument/publishDiagnostics",params={'uri':textDocument['uri'], 'diagnostics': []})


  # クライアントからサーバに 'method': 'textDocument/didChange' が渡った時に実行されるメソッド
  # 全角部分をINFORMATION扱い
  def m_text_document__did_change(self, contentChanges=None, textDocument=None, **_kwargs):
    doc:str = contentChanges[0]['text']
    self.lastDocument = doc
    lines:list[str] = doc.split("\n")
    diagnostics = []
    for i,line in enumerate(lines):
      matches = IS_ZENKAKU.finditer(line)
      for m in matches:
        diagnostics.append({
          'source':'vscpylspext',
          'range':{'start':{'line':i, 'character':m.start()}, 'end':{'line':i, 'character':m.end()}},
          'message':'全角だよ',
          'severity': 3,  # 1~4
          # 'code': ''
          'data': m.group(),
        })
    self.endpoint.notify("textDocument/publishDiagnostics",params={'uri':textDocument['uri'], 'diagnostics': diagnostics})

  # クライアントからサーバに 'method': 'textDocument/didSave' が渡った時に実行されるメソッド
  # 空の通知を送れば全エラーが消える？
  def m_text_document__did_save(self, textDocument=None, **_kwargs):
    self.endpoint.notify("textDocument/publishDiagnostics",params={'uri':textDocument['uri'], 'diagnostics': []})

  def m_text_document__code_action(self, textDocument=None, range=None, context=None, **_kwargs):
    code_actions = []
    changes = []
    for diag in context['diagnostics']:
      if diag['source'] == 'vscpylspext' and diag['message'] == '全角だよ':

        # output = modules.query({
        #   "inputs":  diag['data'],
        # })

        changes.append({
          'range': diag['range'],
          'newText': 'print("Hello World")',
          # 'newText': output[0]["generated_text"]
        })
    if len(changes) > 0:
      code_actions.append({
        'title': 'pythonコードに変換',
        # 'title': output[0]["generated_text"],
        'kind': 'quickfix',
        'diagnostics': [diag],
        'edit': {
          'changes': {
            textDocument['uri'] : changes
          }
        }
      })
    return code_actions


if __name__ == "__main__":
  ls = SampleLanguageServer()
  ls.start()

