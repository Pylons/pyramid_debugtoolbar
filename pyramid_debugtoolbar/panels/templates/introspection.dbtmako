% for category_name, entries in categorized:
<h4>${category_name.capitalize()}</h4>

	% for entry in entries:
	<% intro = entry['introspectable'] %>
	<table>
	<thead>
		<tr>
			<th colspan="2"><a name="${intro.category_name}${intro.discriminator_hash}">${intro.type_name} ${intro.title}</a></th>
		</tr>
	</thead>
	<tbody>
		<% i = 0 %>
		% for k, v in sorted(intro.items()):
		% if v:
		<tr class="${i%2 and 'pDebugEven' or 'pDebugOdd'}">
			<td>${k}</td>
			<td>${debug_repr(v)|n}</td>
		</tr>
		<% i += 1 %>
		% endif
		% endfor
	</tbody>
	<thead>
		<tr>
			<th colspan="2">Source</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td colspan="2">
				<code>${nl2br(str(intro.action_info))|n}</code>
			</td>
		</tr>
	</tbody>
	% if entry['related']:
	<thead>
		<tr>
			<th colspan="2">References</th>
		</tr>
	</thead>
	<tbody>
		% for i, ref in enumerate(entry['related']):
		<tr class="${i%2 and 'pDebugEven' or 'pDebugOdd'}">
			<td colspan="2">
				<a href="#${ref.category_name}${ref.discriminator_hash}">${ref.type_name} ${ref.title}</a>
			</td>
		</tr>
		% endfor
	</tbody>
	% endif
	</table>
	% endfor
% endfor