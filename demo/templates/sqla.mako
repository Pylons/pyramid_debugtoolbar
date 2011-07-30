<html>
    <head>
        <title>${title}</title>
    </head>
    <body>
        <h2>Users</h2>
        % for user in users:
            <p>${user}</p>
        % endfor
    </body>
</html>
