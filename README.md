<img src="assets/banner.svg" alt="fastfetch de atoslins@omarchy: Omarchy · Arch Linux, Hyprland, Araraquara SP. Linux desktop tools, Claude Code plugins, automation." width="100%">

# Atos Lins

Developer from Araraquara, Brazil. I build tools for the Linux desktop
(Omarchy / Hyprland), plugins that keep AI coding agents honest, and the
automation behind a company's day-to-day operations.

> **PT-BR** · Desenvolvedor em Araraquara (SP). Faço ferramentas para o desktop
> Linux (Omarchy / Hyprland), plugins que mantêm agentes de IA honestos e a
> automação do dia a dia de uma empresa.

## Featured · Destaque

### [WhatsApp for Omarchy](https://github.com/atoslins/Omarchy-WhatsApp-v2)

<a href="https://github.com/atoslins/Omarchy-WhatsApp-v2"><img src="https://raw.githubusercontent.com/atoslins/Omarchy-WhatsApp-v2/main/preview.png" alt="WhatsApp for Omarchy: the full app and the bar dropdown" width="100%"></a>

WhatsApp, native to the Omarchy shell. Not a browser tab. Opens instantly and
works offline from a local mirror, replies from the bar, handles several
accounts, and ships an MCP server so agents can read and send messages.
Built on [OmaWhatsApp](https://github.com/MoizIbnYousaf/Omarchy-Whatsapp) by MoizIbnYousaf.

[v0.15.0](https://github.com/atoslins/Omarchy-WhatsApp-v2/releases/tag/v0.15.0) is out ·
[Submitted to the Omarchy plugin store](https://github.com/omacom/omarchy-plugin-marketplace/issues/8842)
<br><sub>WhatsApp nativo no Omarchy, sem aba de navegador: abre na hora, funciona offline e responde pela barra.</sub>

## Contributions · Contribuições

### [Omarchy: Windows VM launch fix](https://github.com/omacom/omarchy/pull/12323)

Merged into [omacom/omarchy](https://github.com/omacom/omarchy) by DHH.
`omarchy windows vm launch` exited 1 with no output whenever `~/Windows` was
setgid, which is how the Windows container itself leaves the folder after the
first run. A numeric `chmod 0700` keeps setgid on directories, so the
exact-mode check could never pass. The fix hardens with a symbolic mode, says
which directory failed and why, and ships regression tests for both paths.
Closes [#9334](https://github.com/omacom/omarchy/issues/9334).
<br><sub>Correção aceita no Omarchy: a VM do Windows falhava em silêncio quando `~/Windows` tinha setgid. Mergeada pelo DHH, com testes de regressão.</sub>

Also: [awesome-claude-code#46](https://github.com/jmanhype/awesome-claude-code/pull/46) and [awesome-claude-plugins#236](https://github.com/composio-community/awesome-claude-plugins/pull/236), DoD-Guard listing.

## Projects · Projetos

### [DualSense for Omarchy](https://github.com/atoslins/omarchy-plugin-dualsense)

<a href="https://github.com/atoslins/omarchy-plugin-dualsense"><img src="https://raw.githubusercontent.com/atoslins/omarchy-plugin-dualsense/main/preview.png" alt="DualSense panel on the Omarchy bar" width="640"></a>

The PS5 DualSense in the Omarchy bar: battery, lightbar, player LEDs, adaptive
triggers, rumble, mic and speaker, plus a live input tester. USB-C and
Bluetooth, no extra packages.
<br><sub>O controle do PS5 na barra do Omarchy: bateria, luzes, gatilhos adaptativos e testador de botões.</sub>

### [Método](https://github.com/atoslins/metodo)

<a href="https://github.com/atoslins/metodo"><img src="https://raw.githubusercontent.com/atoslins/metodo/main/preview.png" alt="Método for Claude Code: the Stop hook stopping a delivery with a blocking gap open, and a gap closing only when its proof command exits 0" width="640"></a>

Claude Code plugin against the three ways coding agents fail to persevere:
giving up at the first obstacle, settling on a solution too early, and
delivering half the job. Three protocols, a gap ledger whose items close only
when a proof command exits 0, and a Stop gate. Measured with and without the
plugin in `claude plugin eval`.

[v1.0.0](https://github.com/atoslins/metodo/releases/tag/metodo--v1.0.0) is out
<br><sub>Plugin do Claude Code contra as três falhas de perseverança de agentes: desistir no primeiro obstáculo, fechar a solução cedo e entregar pela metade.</sub>

### [DoD-Guard](https://github.com/atoslins/dod-guard)

Definition of Done as an executable barrier for Claude Code. Hooks and
read-only reviewer agents stop the agent from declaring a task done while
stubs, skipped tests or unproven claims remain.
<br><sub>Definição de pronto como barreira executável: o agente não declara a tarefa concluída com código pela metade.</sub>

## Stack

Python · TypeScript · PHP · Go · QML / Quickshell · Shell
<br>Linux (Arch / Omarchy) · Docker · PostgreSQL · ClickHouse
