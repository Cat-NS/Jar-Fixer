import os
import sys
import winreg
import subprocess

def find_java():
    """Пытается найти путь к java.exe"""
    # Сначала проверим PATH
    for path in os.environ["PATH"].split(os.pathsep):
        java_exe = os.path.join(path, "java.exe")
        if os.path.isfile(java_exe):
            return java_exe
    # Если не нашли, ищем в реестре (HKLM\SOFTWARE\JavaSoft)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\JavaSoft\Java Runtime Environment")
        current_version, _ = winreg.QueryValueEx(key, "CurrentVersion")
        key_version = winreg.OpenKey(key, current_version)
        java_home, _ = winreg.QueryValueEx(key_version, "JavaHome")
        java_exe = os.path.join(java_home, "bin", "java.exe")
        if os.path.isfile(java_exe):
            return java_exe
    except FileNotFoundError:
        pass
    return None

def set_association(java_path):
    """Создаёт пользовательскую ассоциацию для .jar файлов"""
    # Расширение .jar
    ext = ".jar"
    prog_id = "jarfile"  # произвольный идентификатор класса

    # Открываем (или создаём) ключи в HKCU\Software\Classes
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\\" + ext) as key:
        winreg.SetValue(key, "", winreg.REG_SZ, prog_id)

    # Создаём класс jarfile
    class_key_path = r"Software\Classes\\" + prog_id
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, class_key_path) as key:
        # Описание (необязательно)
        winreg.SetValue(key, "", winreg.REG_SZ, "Java Archive")

    # Команда запуска
    cmd_key_path = class_key_path + r"\shell\open\command"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_key_path) as key:
        # Команда: java -jar "%1" %*
        command = f'"{java_path}" -jar "%1" %*'
        winreg.SetValue(key, "", winreg.REG_SZ, command)

    # Иконка (опционально)
    icon_key_path = class_key_path + r"\DefaultIcon"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, icon_key_path) as key:
        # Можно указать путь к иконке из java.dll или другой
        java_dir = os.path.dirname(java_path)
        icon_path = os.path.join(java_dir, "javaw.exe")  # часто используется
        if not os.path.isfile(icon_path):
            icon_path = java_path  # fallback
        winreg.SetValue(key, "", winreg.REG_SZ, f"{icon_path},0")

    print("Ассоциация успешно установлена для текущего пользователя.")

def main():
    java = find_java()
    if not java:
        print("Java не найдена. Убедитесь, что JRE установлена.")
        sys.exit(1)

    print(f"Найдена Java: {java}")
    try:
        set_association(java)
    except PermissionError:
        print("Ошибка доступа. Возможно, вы запустили скрипт от имени администратора?")
        print("Попробуйте запустить без прав администратора.")
        sys.exit(1)

    # Сообщаем Windows, что ассоциации изменились (чтобы обновить иконки)
    subprocess.run(["ie4uinit.exe", "-show"], capture_output=True)  # для старых Windows
    subprocess.run(["ie4uinit.exe", "-ClearIconCache"], capture_output=True)
    # Альтернатива (более универсальная)
    os.system("taskkill /f /im explorer.exe & start explorer.exe")
    print("Готово! Теперь JAR-файлы должны запускаться двойным щелчком.")

if __name__ == "__main__":
    main()