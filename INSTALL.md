# Installation sans Docker sur une VM dédiée

## Prérequis

- Debian 12.3
- Un utilisateur non-root (ex: `germain`)

---

## Étapes

### 1. Configurer sudo

Se connecter en root :

```bash
su -
apt install sudo git
usermod -aG sudo germain
exit
exit
```

Se reconnecter avec l'utilisateur `germain`.

### 2. Installer OpenSSH pour l'administration distante

```bash
sudo apt update && sudo apt install openssh-server -y
```

### 3. Cloner le code source et lancer le script d'installation

```bash
git clone --filter=blob:none --sparse --depth=1 git@github.com:germainm/egyptian.git /tmp/egyptian-install
git -C /tmp/egyptian-install sparse-checkout set mayan requirements
sudo bash /tmp/egyptian-install/mayan/install.sh
rm -rf /tmp/egyptian-install
```

Le script pose les questions suivantes :

| Section | Paramètres |
|---------|-----------|
| PostgreSQL | nom DB, utilisateur, mot de passe, hôte |
| RabbitMQ | utilisateur, mot de passe, vhost, hôte, port |
| Redis | mot de passe, hôte, port |
| Elasticsearch | activation (o/n), URL, port, utilisateur, mot de passe, SSL |
| OIDC | activation (o/n), URL du profil utilisateur |
| Nginx + SSL | activation (o/n), nom de domaine, email Let's Encrypt |
| Général | fuseau horaire, hôte autorisé |

> **Note :** Éviter les caractères `"`, `'`, `$`, `` ` `` dans les mots de passe.

Le script génère :
- `/etc/supervisor/conf.d/egyptian.conf` — config Supervisor avec les mots de passe (accessible root uniquement)
- `/opt/egyptian/media/config.yml` — paramètres non-sensibles de l'application
