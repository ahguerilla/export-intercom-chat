import urllib.request, json
import requests
import csv
from datetime import datetime

API_KEY =  ## API KEY HERE -- update to arg


def get_headers():
  headers = dict()
  headers["Authorization"] = "Bearer " + API_KEY
  headers["Accept"] = "application/json"
  return headers

def parse_author(author):
  return {
    "author_type": author.get("type"),
    "name": author.get("name"),
    "email": author.get("email"),
  }

def parse_source(source, created):
  psource = parse_author(source.get("author"))
  psource.update({
    "type": source.get("delivered_as"),
    "created": created,
    "subject": source.get("subject"),
    "body": source.get("body"),
    "redacted": source.get("redacted"),
  })
  return psource

def parse_conversation_part(conversation_part):
  pconvo_part = parse_author(conversation_part.get("author"))
  pconvo_part.update({
    "type": conversation_part.get("part_type"),
    "created": conversation_part.get("created_at"),
    "subject": conversation_part.get("subject"),
    "body": conversation_part.get("body"),
    "redacted": conversation_part.get("redacted"),
  })
  return pconvo_part  


def parse_individual_conversation(conversation_id):
  url = "https://api.intercom.io/conversations/" + str(conversation_id)
  response = requests.get(url=url, headers=get_headers())
  response_json = response.json()
  parts = [] 

  parts.append(parse_source(response_json.get("source"), response_json.get("created_at")))
  for conversation_part in response_json.get("conversation_parts").get("conversation_parts"):
    parts.append(parse_conversation_part(conversation_part))

  return {
    "id": response_json.get("id"),
    "parts": parts,
  }


def get_all_conversation():
  url = "https://api.intercom.io/conversations?order=desc&sort=updated_at"
  list_conversations = []
  while url:
    try:
      response = requests.get(url=url, headers=get_headers())
    except Exception as ex:
      # seems intercom API throws the occasional error
      # not updating the URL will cause a retry
      continue
    url = response.json().get("pages").get("next")
    for conversation in response.json().get("conversations"):
      list_conversations.append(parse_individual_conversation(conversation.get("id")))
  return list_conversations

def main():
  conversations = get_all_conversation()
  with open('intercom.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csvwriter.writerow(['Conversation ID', 'Date', 'Message Type', 'Subject', 'Body', 'Redacted', 'Author', 'Author Email', 'Author Type'])
    for c in conversations:
      first_loop = True
      for p in c.get('parts'):
        convo_id = c.get("id") if first_loop else ""
        first_loop = False
        csvwriter.writerow([convo_id, datetime.utcfromtimestamp(p.get("created")).strftime('%Y-%m-%d %H:%M:%S'), 
          p.get("type"), p.get("subject"), p.get("body"), p.get("redacted"), p.get("name"), p.get("email"), p.get("author_type")])


if __name__ == '__main__':
    main()



