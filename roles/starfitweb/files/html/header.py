def http():
    print("Content-Type: text/html; charset=UTF-8")
    print('Cache-Control: "no-cache, no-store, must-revalidate"')
    print(
        "Content-Security-Policy: default-src https: data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;"
    )
    print()
