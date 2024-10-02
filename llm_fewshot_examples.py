few_shots = {
    # en_de_#CLIENT-01#_default_2020-12-20-12,10
    "ende_gemba": {
            "source_lang": "English",
            "source_seg": "I do apologise about this, we must gain permission from the account holder to discuss an order with another person, I apologise if this was done previously, however, I would not be able to discuss this with yourself without the account holders permission.",
            "target_lang": "German",
            "target_seg": "Ich entschuldige mich dafür, wir müssen die Erlaubnis einholen, um eine Bestellung mit einer anderen Person zu besprechen. Ich entschuldige mich, falls dies zuvor geschehen wäre, aber ohne die Erlaubnis des Kontoinhabers wäre ich nicht in der Lage, dies mit dir involvement.",
            "answer": """Critical:
no-error
Major:
accuracy/mistranslation - "involvement"
accuracy/omission - "the account holder"
Minor:
fluency/grammar - "wäre"
fluency/register - "dir"
""",
        },
    "ende_conversation_1": {
            "source_lang": "English",
            "source_seg": "As soon as we have heard back, tis is when you will be emailed",
            "target_lang": "German",
            "target_seg": "Sobald wir wieder gehört haben, tis ist, wenn Sie e-mail erhalten werden",
            "answer": """Critical:
accuracy/untranslated - "tis"
Major:
accuracy/mistranslation - "wieder gehört haben"
Minor:
accuracy/addition - "wenn"
source issue - "tis"
""",
        },
}

def mqm_fewshot(few_shots):
    prompts = [
        {
            "role": "system",
            "content": f"You are an annotator for the quality of machine translation. Your task is to identify errors and assess the quality of the translation.\n The categories of errors are: accuracy (addition, mistranslation, omission, untranslated text), fluency (character encoding, grammar, inconsistency, punctuation, register, spelling), style (awkward), terminology (inappropriate for context, inconsistent use), non-translation, other, source error or no-error.\nEach error is classified as one of three categories: critical, major, and minor. Critical errors inhibit comprehension of the text. Major errors disrupt the flow, but what the text is trying to say is still understandable. Minor errors are technically errors, but do not disrupt the flow or hinder comprehension."
        }
    ]

    template = """{source_lang} source:
```{source_seg}```
{target_lang} translation:
```{target_seg}```

Based on the source segment and machine translation surrounded with triple backticks, identify error types in the translation and classify them."""

    for shot in few_shots:
        prompts.append({
            "role": "user",
            "content": template.format(**shot)
        })
        answer = shot['answer']

        prompts.append({
            "role": "assistant",
            "content": answer
        })

    prompts.append({
            "role": "user",
            "content": template
        })

    return prompts

# all context in source, source+hyp in the context
few_shots_context = {
    "ende_conversation_1": {
            "source_lang": "English",
            "source_seg": "As soon as we have heard back, tis is when you will be emailed",
            "target_lang": "German",
            "target_seg": "Sobald wir wieder gehört haben, tis ist, wenn Sie e-mail erhalten werden",
            "sender": "Agent",
            "context": """Customer (German): Hallo, ich habe einen Artikel, der letzte Woche geliefert werden sollte und der immer noch nicht geliefert wird.
Customer (German): Ich habe den Chat zweimal kontaktiert und bisher nichts.
Customer (German): Die First Lady sagte mir, dass es am Montag verschickt wird, die zweite Lady sagte mir gestern, dass sie eine E-Mail überprüfen und senden wird und sie hat nie geantwortet.
Customer (German): #ADDRESS#,
Agent (English): Good Morning #NAME#
Agent (English): Thanks for contacting #PRS_ORG#, you are through to #NAME#
Agent (English): So that I can assist you can you please provide your account details (Full Name, E-mail address, Postal Address and Order Number)
Customer (German): Bestellnummer: #NUMBER#
Customer (German): #ADDRESS#
Agent (English): Thank you - so this query is with warehouse as stated in yesterdays chat, we have to await the reply to the investigation.
""",
            "answer": """Critical:
accuracy/untranslated - "tis"
Major:
accuracy/mistranslation - "wieder gehört haben"
Minor:
accuracy/addition - "wenn"
source issue - "tis"
""",
        },
}


def mqm_fewshot_context(few_shots):
    prompts = [
        {
            "role": "system",
            "content": f"You are an annotator for the quality of machine translation. Your task is to identify errors and assess the quality of the translation.\n The categories of errors are: accuracy (addition, mistranslation, omission, untranslated text), fluency (character encoding, grammar, inconsistency, punctuation, register, spelling), style (awkward), terminology (inappropriate for context, inconsistent use), non-translation, other, source error or no-error.\nEach error is classified as one of three categories: critical, major, and minor. Critical errors inhibit comprehension of the text. Major errors disrupt the flow, but what the text is trying to say is still understandable. Minor errors are technically errors, but do not disrupt the flow or hinder comprehension."
        }
    ]

    template = """Context:
```{context}```
{sender} source ({source_lang}):
```{source_seg}```
{target_lang} translation:
```{target_seg}```

Based on the conversation context between the agent and the customer, the current source by "{sender}" in {source_lang} and its machine translation in {target_lang} surrounded with triple backticks, identify error types in the translation and classify them."""

    for shot in few_shots:
        prompts.append({
            "role": "user",
            "content": template.format(**shot)
        })
        answer = shot['answer']

        prompts.append({
            "role": "assistant",
            "content": answer
        })

    prompts.append({
            "role": "user",
            "content": template
        })

    return prompts

TEMPLATE_GEMBA_MQM_1shot = mqm_fewshot([few_shots['ende_conversation_1']])
TEMPLATE_GEMBA_CONTEXT_MQM_1shot = mqm_fewshot_context([few_shots_context['ende_conversation_1']])